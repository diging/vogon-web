"""
Provides views related to external repositories.
"""
from rest_framework import viewsets

from annotations.serializers import RepositorySerializer
from repository.models import Repository


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
