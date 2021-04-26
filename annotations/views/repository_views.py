"""
Provides views related to external repositories.
"""
from rest_framework import viewsets
from rest_framework.response import Response

from annotations.serializers import RepositorySerializer, ProjectSerializer, TextCollection
from annotations.views.utils import get_project_details
from repository.models import Repository


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer

    def list(self, request):
        project = get_project_details(request)
        if not project:
            return Response({
                "message": "Project not found!"
            }, 404)
        
        queryset = self.get_queryset()
        serializer = RepositorySerializer

        self.page = self.paginate_queryset(queryset)
        if self.page is not None:
            serializer = RepositorySerializer(self.page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            response = Response(serializer(queryset, many=True).data)
        
        response.data['project'] = ProjectSerializer(project).data
        return response