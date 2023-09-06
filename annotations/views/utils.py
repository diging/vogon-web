from annotations.serializers import TextCollection
from annotations.models import *
from django.shortcuts import get_object_or_404

def get_project_details(request):
    project_id = request.query_params.get('project_id', None)
    if project_id:
        try:
            return TextCollection.objects.get(pk=project_id)
        except TextCollection.DoesNotExist:
            return None
    
    # Return user's default project
    return request.user.get_default_project()

def get_params(request, pk):
    template = get_object_or_404(RelationTemplate, pk=pk)
    data = request.data
    text = get_object_or_404(Text, pk=data['occursIn'])
    
    project_id = data.get('project', None)
    if project_id is None:
        project_id = VogonUserDefaultProject.objects.get(
            for_user=request.user).project.id
    
    return template, data, request.user, text, project_id