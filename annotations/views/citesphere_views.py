from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from annotations.serializers import RepositorySerializer, TextSerializer, RelationSetSerializer
from repository.models import Repository


class CitesphereRepoViewSet(viewsets.ViewSet):
    queryset = Repository.objects.all()

    def retrieve(self, request, pk):
        queryset = Repository.objects.filter(repo_type=Repository.CITESPHERE)
        repository = get_object_or_404(queryset, pk=pk)

        manager = repository.manager(request.user)
        groups = manager.groups()

        return Response({
            **RepositorySerializer(repository).data,
            'groups': groups
        })


class CitesphereGroupsViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        groups = manager.groups()
        return Response(groups)