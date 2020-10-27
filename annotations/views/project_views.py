"""
Provides project (:class:`.TextCollection`) -related views.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from annotations.models import TextCollection, RelationSet, Text, Appellation
from annotations.serializers import TextCollectionSerializer, ProjectTextSerializer, ProjectSerializer
from repository.models import Repository


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = TextCollection.objects.all()
    serializer_class = TextCollectionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('ownedBy__username',)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectTextSerializer(project)
        return Response(serializer.data)

    def create(self, request):
        request.data['ownedBy'] = request.user.pk
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['POST'], url_name='addtext')
    def add_text(self, request, pk=None):
        text_id = request.data['text_id']
        repo_id = request.data['repository_id']

        repository = get_object_or_404(Repository, pk=repo_id)
        project = get_object_or_404(TextCollection, pk=pk)
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

    def destroy(self, request, pk=None):
        text_id = request.data['text_id']

        submitted = Appellation.objects.filter(occursIn_id=text_id, submitted=True)
        if submitted:
            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        project = get_object_or_404(TextCollection, pk=pk)
        project.texts.filter(pk=text_id).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

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
