"""
Provides views related to external repositories.
"""
from rest_framework import viewsets

from annotations.serializers import RepositorySerializer
from repository.models import Repository

def get_project_details(request):
    project_id = request.query_params.get('project_id', None)
    if project_id:
        try:
            return TextCollection.objects.get(pk=project_id)
        except TextCollection.DoesNotExist:
            return None
    
    # Return user's default project
    return request.user.get_default_project()

class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
