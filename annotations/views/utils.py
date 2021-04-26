from annotations.serializers import TextCollection

def get_project_details(request):
    project_id = request.query_params.get('project_id', None)
    if project_id:
        try:
            return TextCollection.objects.get(pk=project_id)
        except TextCollection.DoesNotExist:
            return None
    
    # Return user's default project
    return request.user.get_default_project()