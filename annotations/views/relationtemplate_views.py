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
from rest_framework.permissions import IsAdminUser
from annotations.models import *
from annotations import relations
from annotations.serializers import TemplatePartSerializer, TypeSerializer, TemplateSerializer
from concepts.models import Concept, Type
from goat.views import retrieve as retrieve_concept
from .utils import get_relationset_params


logger = logging.getLogger(__name__)
logger.setLevel('ERROR')

class RelationTemplateViewSet(viewsets.ModelViewSet):
    queryset = RelationTemplate.objects.all()
    serializer_class = TemplatePartSerializer
    permission_classes = (IsAdminUser,)

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

    @action(detail=True, methods=['post'], url_name='createrelation')
    def create_relation(self, request, pk=None):
        params = get_relationset_params(request, pk)
        
        relationset = relations.create_relationset(
            template=params[0], raw_data=params[1], creator=params[2], text=params[3], project_id=params[4]
        )
        return JsonResponse({ 'relationset_id': relationset.id })
    
    @action(detail=True, methods=['put'], url_name='update_relation')
    def update_relation(self, request, pk=None):
        relationset_id = request.data['relation_id']
        params = get_relationset_params(request, pk)
        
        relationset = relations.update_relationset(
            template=params[0], raw_data=params[1], creator=params[2], text=params[3], project_id=params[4], relationset_id=relationset_id
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
            queryset = queryset.filter(createdBy=self.request.user.id)
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
                    if concept_type_id:
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

    @action(detail=False, url_name='createform')
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
        