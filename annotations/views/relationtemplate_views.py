"""
Provides :class:`.RelationTemplate`\-related views.
"""

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
from string import Formatter

from annotations.forms import (RelationTemplatePartFormSet,
                               RelationTemplatePartForm, RelationTemplateForm)
from annotations.models import *
from annotations import relations
from concepts.models import Concept, Type

import copy
import json
import logging
import networkx as nx

logger = logging.getLogger(__name__)
logger.setLevel('ERROR')


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


@login_required
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
