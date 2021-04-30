"""
Provides project (:class:`.TextCollection`) -related views.
"""
import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from annotations.models import TextCollection, RelationSet, Text, Appellation, RelationTemplate
from accounts.models import VogonUser
from annotations.serializers import (
    TextCollectionSerializer, ProjectTextSerializer, ProjectSerializer, 
    VogonUserSerializer, VogonUserDefaultProject
)
from annotations.filters import ProjectFilter
from repository.models import Repository


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = TextCollection.objects.all()
    serializer_class = TextCollectionSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = ProjectFilter

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        response = ProjectTextSerializer(project).data
        response['is_default'] = self._is_default_project(request, project)
        return Response(response)

    def create(self, request):
        request.data['createdBy'] = request.user
        request.data['ownedBy'] = request.user
        project = TextCollection(**request.data)
        project.save()
        response = ProjectSerializer(project).data
        return Response(response, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'], url_name='addtext')
    def add_text(self, request, pk=None):
        text_id = request.data['text_id']
        repo_id = request.data['repository_id']

        repository = get_object_or_404(Repository, pk=repo_id)
        project = get_object_or_404(TextCollection, pk=pk)
        
        if project.ownedBy.id != request.user.id:
            return Response(
                { "error": "User not authorized to add text" },
                403
            )

        manager = repository.manager(request.user)
        resource = manager.resource(resource_id=int(text_id))

        defaults = {
            'title': resource.get('title'),
            'created': resource.get('created'),
            'repository': repository,
            'repository_source_id': text_id,
            'addedBy': request.user,
        }
        text, _ = Text.objects.get_or_create(uri=resource.get('uri'),
                                             defaults=defaults)
        project.texts.add(text)
        
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_name='changeownership')
    def change_ownership(self, request, pk=None):
        project = get_object_or_404(TextCollection, pk=pk)
        
        # Reject request if current user is not the project owner
        if project.ownedBy.id != request.user.id:
            return Response(
                { "message": "User unauthorized to change ownership" },
                403
            )
        
        target_user_id = request.data.get('target_user_id')
        if not target_user_id:
            return Response(
                { "message": "Specify the user id to whom you would like to change the ownership" },
                400
            )
        
        try:
            # Change owner to `target_user`, make current user as participant
            target_user = VogonUser.objects.get(pk=target_user_id)
            project.ownedBy = target_user
            project.participants.add(request.user)
            project.participants.remove(target_user)
            project.save(force_update=True)
            return Response(
                { "message": f"Successfully changed project ownership to user_id='{target_user.username}'" }
            )
        except VogonUser.DoesNotExist:
            return Response(
                { "message": f"Could not find user with id {target_user_id}!" },
                404
            )

    @action(detail=False, methods=['get'], url_name='userprojectlist')
    def list_user_projects(self, request):
        project_id = request.query_params.get('project_id', None)
        query = request.query_params.get('q', None)

        if project_id:
            project = TextCollection.objects.get(pk=project_id)
        else:
            project = request.user.get_default_project()
        owned_projects = request.user.collections.filter(~Q(id=project.id))
        contributing_projects = request.user.contributes_to.all()
        
        user_projects = (owned_projects | contributing_projects).distinct()
        if query:
            user_projects = user_projects.filter(name__icontains=query)

        serializer = ProjectSerializer(user_projects, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, pk=None):
        text_id = request.data['text_id']

        submitted = Appellation.objects.filter(occursIn_id=text_id, submitted=True)
        if submitted:
            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        project = get_object_or_404(TextCollection, pk=pk)
        project.texts.filter(pk=text_id).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_name='setasdefault')
    def set_as_default(self, request, pk=None):
        project = get_object_or_404(TextCollection, pk=pk)
        if project.ownedBy != request.user:
            return Response({
                "message": "User not authorized to set project as default"
            }, 403)

        request.user.set_default_project(project)
        return Response({
            "message": f"Successfully set as your default project - '{project.name}'"
        })
    
    @action(detail=True, methods=['GET'], url_name='export_affiliations')
    def export_affiliations(self, request, pk=None):
        project = get_object_or_404(TextCollection, pk=pk)
        template = RelationTemplate.objects.get(pk=settings.AFFILIATION_TEMPLATE_ID)

        relationsets = RelationSet.objects.filter(
            project=project,
            template=template,
            createdBy=request.user,
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="affiliations.csv"'
        
        fieldnames = ['project', 'created', 'text', 'affiliation', 'author']
        writer = csv.writer(response)
        writer.writerow(fieldnames)

        for relationset in relationsets:
            relations = relationset.constituents.all().order_by('id')[:2]
            writer.writerow([
                project.name, relationset.created, relationset.occursIn.title,
                relations[0].object_content_object.stringRep,
                relations[1].source_content_object.stringRep
            ])
        
        return response

    def get_queryset(self):
        queryset = super(ProjectViewSet, self).get_queryset()
        queryset = queryset.annotate(
            num_texts=Count('texts'),
            num_relations=Count('texts__relationsets')
        )
        return queryset

    def get_paginated_response(self, data):
        return Response({
            'count':len(self.filter_queryset(self.get_queryset())),
            'results': data
        })

    def _is_default_project(self, request, project):
        return VogonUserDefaultProject.objects.filter(
            for_user=request.user,
            project=project
        ).exists()
