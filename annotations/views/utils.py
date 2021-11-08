from annotations.serializers import TextCollection
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from annotations import annotators
from annotations.models import Text, TextCollection, RelationSet, Appellation
from annotations.serializers import RepositorySerializer, TextSerializer, RelationSetSerializer, ProjectSerializer
from repository.models import Repository
from django.db.models import Q
from rest_framework.exceptions import APIException
from django.db import transaction

def get_project_details(request):
    project_id = request.query_params.get('project_id', None)
    if project_id:
        try:
            return TextCollection.objects.get(pk=project_id)
        except TextCollection.DoesNotExist:
            return None
    
    # Return user's default project
    return request.user.get_default_project()
    
def _get_project(request, field):
    project_id = request.data.get(field, None)
    if not project_id:
        raise APIException({
            "message": f"Could not find `{field}` in request body",
            "code": 400
        })
    try:
        return TextCollection.objects.get(pk=project_id)
    except TextCollection.DoesNotExist:
        raise APIException({
            "message": f"Project with id=`{project_id}` not found!", 
            "code": 404
        })

def _transfer_text(text, current_project, target_project, user):
    # Check eligibility
    is_owner = user.pk == current_project.ownedBy.pk
    is_target_contributor = target_project.participants.filter(pk=user.pk).exists()
    is_target_owner = target_project.ownedBy.pk == user.pk
    if not is_owner:
        raise APIException({
            "message": f"User is not the owner of current project '{current_project.name}'",
            "code": 403
        })
    if not (is_target_contributor or is_target_owner):
        raise APIException({
            "message": f"User is not owner/contributor of target project '{target_project.name}'",
            "code": 403
        })

    # Check if text is already part of `target_project`
    if target_project.texts.filter(pk=text.pk).exists():
        raise APIException({
            "message": f"Text `{text.title}` is already part of project `{target_project.name}`!",
            "code": 403
        })

        # Retrieve all related objects for `current_project`
    appellations = Appellation.objects.filter(
        occursIn__in=text.children,
        project=current_project
    )
    relationsets = RelationSet.objects.filter(
        occursIn__in=text.children,
        project=current_project
    )

    with transaction.atomic():
        appellations.update(project=target_project)
        relationsets.update(project=target_project)
        for child in text.children:
            child_text = Text.objects.get(pk=child)
            current_project.texts.remove(child_text)
            target_project.texts.add(child_text)
            
        current_project.save(force_update=True)
        target_project.save(force_update=True)
    
def _get_project_details(request, pk):
    project = get_project_details(request)
    if not project:
        return False, None, None

    project_details = ProjectSerializer(project).data
    part_of_project = None
    texts = Text.objects.filter(pk__in=project_details['texts'])
    if texts:
        part_of_project = project_details
        return True, project_details, part_of_project
