"""
Provides :class:`.RelationTemplate`\-related views.
"""
import copy
import json
import logging
import networkx as nx
from string import Formatter
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db.models import Q
from django.db import transaction, DatabaseError
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from annotations.forms import (RelationTemplatePartFormSet,
                               RelationTemplatePartForm, RelationTemplateForm)
from annotations.models import *
from annotations import relations
from annotations.serializers import TemplatePartSerializer, TypeSerializer, TemplateSerializer
from concepts.models import Concept, Type
from goat.views import retrieve as retrieve_concept


logger = logging.getLogger(__name__)
logger.setLevel('ERROR')

class RelationTemplateViewSet(viewsets.ModelViewSet):
    queryset = RelationTemplate.objects.all()
    serializer_class = TemplatePartSerializer

    def list(self, request):
        data = self.get_queryset()
        serializer = TemplatePartSerializer(data, many=True)
        result = serializer.data
        return Response(result)

    def retrieve(self, request, pk=None):
        queryset = RelationTemplate.objects.all()
        template = get_object_or_404(queryset, pk=pk)
        serializer = TemplateSerializer(template)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_relation(self, request, pk=None):
        template = get_object_or_404(RelationTemplate, pk=pk)
        data = request.data
        text = get_object_or_404(Text, pk=data['occursIn'])
        
        project_id = data.get('project', None)
        if project_id is None:
            project_id = VogonUserDefaultProject.objects.get(
                for_user=request.user).project.id
        
        relationset = relations.create_relationset(
            template, data, request.user, text, project_id
        )
        return JsonResponse({ 'relationset_id': relationset.id })

    def get_queryset(self, *args, **kwargs):
        queryset = super(RelationTemplateViewSet, self).get_queryset(*args, **kwargs)
        search = self.request.query_params.get('search', None)
        all_templates = self.request.query_params.get('all', False)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        if not all_templates:
            queryset = queryset.filter(createdBy=self.request.user)
        data = [
            {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'fields': relations.get_fields(item),
            } for item in queryset.order_by('-id')
        ]
        return data

    def create(self, request):
        return self.create_or_update(request)
    
    def update(self, request, pk=None):
        queryset = RelationTemplate.objects.all()
        template = get_object_or_404(queryset, pk=pk)
        if template:
            request.data['id'] = template.id
            return self.create_or_update(request)

    def destroy(self, request, pk=None):
        if not RelationSet.objects.filter(template_id=pk):
            try:
                with transaction.atomic():
                    RelationTemplate.objects.filter(
                        id=pk
                    ).delete()
                    RelationTemplatePart.objects.filter(
                        part_of=pk
                    ).delete()
            except DatabaseError:
                return Response({
                    'success': False,
                    'error': 'There was an error while deleting the relation template. Please redo the operation.'
                }, status=500)
        else:
            return Response({
                'success': False,
                'error': 'Could not delete relation template because there is data associated with it'
            }, status=500)

        return Response({
            'success': True
        })
    
    def create_or_update(self, request):
        data = request.data
        template_data = {
            'name': data.get('name', None),
            'description': data.get('description', ''),
            'expression': data.get('expression', ''),
            'terminal_nodes': data.get('terminal_nodes', ''),
            'createdBy': request.user,
        }
        if data.get('id', None):
            template_data['id'] = data['id']
        
        # Create required concepts
        for part in data.get('parts', []):
            for field in ['source', 'predicate', 'object']:
                node_type = part[f'{field}_node_type']
                if node_type == 'CO':
                    concept = self.add_concept(part[f'{field}_concept'])
                    part[f'{field}_concept'] = concept
                elif node_type == 'TP':
                    concept_type_id = part[f'{field}_type']
                    concept_type = Type.objects.get(pk=concept_type_id)
                    part[f'{field}_type'] = concept_type
                if field != 'predicate':
                    internal_id = part[f'{field}_relationtemplate_internal_id']
                    part[f'{field}_relationtemplate_internal_id'] = int(internal_id)

        try:
            template = relations.create_template(
                template_data,
                data.get('parts', [])
            )
            return Response({
                'success': True,
                'template_id': template.id
            })
        except relations.InvalidTemplate as E:
            return Response({
                'success': False,
                'error': str(E)
            }, status=500)

    @action(detail=False)
    def create_form(self, request):
        types = Type.objects.all()
        return Response({
            'open_concepts': TypeSerializer(types, context={'request': request}, many=True).data
        })

    def add_concept(self, concept):
        uri = concept['uri']
        try:
            # Try to find the concept in vogon by `uri`
            result = Concept.objects.get(uri=uri)
        except Concept.DoesNotExist:
            # Find the concept from Goat by `uri`
            concept = retrieve_concept(uri)
            data = dict(
                uri=uri,
                label=concept['name'],
                description=concept['description'],
            )
            ctype_data = concept['concept_type']
            if ctype_data:
                data.update({
                    'typed': Type.objects.get_or_create(
                        uri=ctype_data['identifier'],
                        label=ctype_data['identifier']
                    )[0]
                })

            # Create the concept object in vogon
            result = Concept.objects.create(**data)
        
        return result
        

@staff_member_required
def add_relationtemplate(request):
    """
    Staff can use this view to create :class:`.RelationTemplate`\s.

    Parameters
    ----------
    project_id : int
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    formset = formset_factory(
        RelationTemplatePartForm, formset=RelationTemplatePartFormSet)
    form_class = RelationTemplateForm  # e.g. Name, Description.

    context = {}

    if request.POST:
        logger.debug('add_relationtemplate: post request')
        # Instatiate both form(set)s with data.
        relationtemplatepart_formset = formset(request.POST, prefix='parts')
        relationtemplate_form = form_class(request.POST)
        context['formset'] = relationtemplatepart_formset
        context['templateform'] = relationtemplate_form

        formset_is_valid = relationtemplatepart_formset.is_valid()
        form_is_valid = relationtemplate_form.is_valid()

        if formset_is_valid and form_is_valid:
            relationtemplate_data = dict(relationtemplate_form.cleaned_data)
            relationtemplate_data['createdBy'] = request.user
            part_data = [
                dict(form.cleaned_data)
                for form in relationtemplatepart_formset
            ]

            try:
                # relations.create_template() calls validation methods.
                template = relations.create_template(relationtemplate_data,
                                                     part_data)
                return HttpResponseRedirect(
                    reverse('get_relationtemplate', args=(template.id, )))
            except relations.InvalidTemplate as E:
                relationtemplate_form.add_error(None, E.message)
                logger.debug(
                    'creating relationtemplate failed: %s' % (E.message))
        context['formset'] = relationtemplatepart_formset
        context['templateform'] = relationtemplate_form

    else:  # No data, start with a fresh formset.
        context['formset'] = formset(prefix='parts')
        context['templateform'] = form_class()

    return render(request, 'annotations/relationtemplate.html', context)

@api_view(['GET'])
def list_relationtemplate(request):
    """
    Returns a list of all :class:`.RelationTemplate`\s.

    This view will return JSON if ``format=json`` is passed in the GET request.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    queryset = RelationTemplate.objects.all()
    search = request.GET.get('search', None)
    all_templates = request.GET.get('all', False)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search))
    if not all_templates:
        queryset = queryset.filter(createdBy=request.user)

    data = {
        'templates': [{
            'id': rt.id,
            'name': rt.name,
            'description': rt.description,
            'fields': relations.get_fields(rt),
        } for rt in queryset.order_by('-id')]
    }
    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = "annotations/relationtemplate_list.html"
    context = {
        'user': request.user,
        'data': data,
        'all_templates': all_templates
    }

    return render(request, template, context)


@login_required
def get_relationtemplate(request, template_id):
    """
    Returns data on fillable fields in a :class:`.RelationTemplate`\.

    This view will return JSON if ``format=json`` is passed in the GET request.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    template_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    relation_template = get_object_or_404(RelationTemplate, pk=template_id)

    data = {
        'fields': relations.get_fields(relation_template),
        'name': relation_template.name,
        'description': relation_template.description,
        'id': template_id,
        'expression': relation_template.expression,
    }
    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = "annotations/relationtemplate_show.html"
    context = {
        'user': request.user,
        'data': data,
    }

    return render(request, template, context)


@login_required
def create_from_relationtemplate(request, template_id):
    """
    Create a :class:`.RelationSet` and constituent :class:`.Relation`\s from
    a :class:`.RelationTemplate` and user annotations.

    This is mainly used by the RelationTemplateController in the text
    annotation  view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    template_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    # TODO: this could also use quite a bit of attention in terms of
    #  modularization.
    template = get_object_or_404(RelationTemplate, pk=template_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        text = get_object_or_404(Text, pk=data['occursIn'])
        project_id = data.get('project')
        if project_id is None:
            project_id = VogonUserDefaultProject.objects.get(
                for_user=request.user).project.id
        relationset = relations.create_relationset(
            template, data, request.user, text, project_id)
        response_data = {'relationset': relationset.id}
    else:  # Not sure if we want to do anything for GET requests at this point.
        response_data = {}

    return JsonResponse(response_data)


def create_from_text(request, template_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        appellations = data['appellations']
        text_appellation = data['textAppellation']
        template = get_object_or_404(RelationTemplate, pk=template_id)
        text = get_object_or_404(Text, pk=data['occursIn'])
        project_id = data.get('project')
        if project_id is None:
            project_id = VogonUserDefaultProject.objects.get(
                for_user=request.user).project.id
        for appellation in appellations:
            #FIXME: Hardcoding this data object is not good practice
            # but will work for the time being
            appellation_object = {
                'end':
                None,
                'fields': [
                    {
                        'appellation': text_appellation,
                        'part_field': 'source',
                        'description': '',
                        'concept_label': None,
                        'evidence_reqired': False,
                        'label': 'Text',
                        'part_id': data['part_id'],
                        'type': 'TP',
                        'concept_id': None
                    },
                    {
                        'appellation': appellation,
                        'part_field': 'object',
                        'description': '',
                        'concept_label': None,
                        'evidence_reqired': True,
                        'label': 'Concept',
                        'part_id': data['part_id'],
                        'type': 'TP',
                        'concept_id': None
                    }
                ],
                'occrsIn':
                data['occursIn'],
                'project':
                data['project'],
                'start':
                None,
                'createdBy':
                str(request.user.id),
                'occur':
                None
            }
            relationset = relations.create_relationset(
                template, appellation_object, request.user, text, project_id)
            response_data = {'relationset': relationset.id}
        else:  # Not sure if we want to do anything for GET requests at this point.
            response_data = {}

    return JsonResponse(response_data)


@staff_member_required
def delete_relationtemplate(request, template_id):
    if request.method == 'POST':

        # Check if there is relation template is associated with a relation set before deleting it
        if not RelationSet.objects.filter(template_id=template_id):
            try:
                with transaction.atomic():
                    RelationTemplate.objects.filter(id=template_id).delete()
                    RelationTemplatePart.objects.filter(
                        part_of=template_id).delete()
            except DatabaseError:
                messages.error(
                    request,
                    'ERROR: There was an error while deleting the relation template. Please redo the operation.'
                )
        else:
            messages.error(
                request,
                'ERROR: Could not delete relation template because there is data associated with it'
            )

    return HttpResponseRedirect(reverse('list_relationtemplate'))
