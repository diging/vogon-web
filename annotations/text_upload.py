
from annotations.models import Text, TextCollection, RelationSet
from repository.models import Repository
from repository.managers import RepositoryManager
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.response import Response
from annotations import annotators

'''
This files contains helper functions to add text from uploaded documents to a users repository and project
'''



def repository_text_content(user, repository_id, text_id, content_id, part_of_id, project_id):
    '''
    Takes a text from amphora and adds it to a users repository.
    
    Parameters
    ----------
    user : vogon user
    repository_id : defaults to 1
    text_id : the text id from amphora
    content_id : content id from amphora
    part_of_id : id of project the text is to be apart of
    '''
    repository = get_object_or_404(Repository, pk=repository_id)

    manager = RepositoryManager(repository.configuration, user=user)
    try:
        content = manager.content(id=int(content_id))
        resource = manager.resource(id=int(text_id))
    except IOError:
        return False

    content_type = content.get('content_type', None)
    if not annotators.annotator_exists(content_type):
        return False
    resource_text_defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': text_id,
        'addedBy': user,
    }
    
    if part_of_id:
        try:
            master = manager.resource(id=int(part_of_id))
        except IOError:
            return False
        master_resource, _ = Text.objects.get_or_create(uri=master['uri'],
                                                        defaults={
            'title': master.get('title'),
            'created': master.get('created'),
            'repository': repository,
            'repository_source_id': part_of_id,
            'addedBy': user,
        })
        resource_text_defaults.update({'part_of': master_resource})

    resource_text, _ = Text.objects.get_or_create(uri=resource['uri'], defaults=resource_text_defaults)

    
    if project_id:
        project = TextCollection.objects.get(pk=project_id)
    else:
        project = None

    target, headers = content.get('location'), {}

    defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': content_id,
        'addedBy': user,
        'content_type': content_type,
        'part_of': resource_text,
        'originalResource': getattr(resource.get('url'), 'value', None),
    }
    text, _ = Text.objects.get_or_create(uri=content['uri'], defaults=defaults)
    if project_id:
        project.texts.add(text.top_level_text)
    return True

def add_text_to_project(user, repository_id, text_id, project_id):

    '''
    adds a text from a repository to a project

    Parameters
    ----------
    user : vogon user
    repository_id : defaults to 1
    text_id : the text id from amphora
    '''
    repository = get_object_or_404(Repository, pk=repository_id)
    project = get_object_or_404(TextCollection, pk=project_id)

    manager = RepositoryManager(repository.configuration, user=user)
    try:
        resource = manager.resource(id=int(text_id))
    except IOError:
        return False
    defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': text_id,
        'addedBy': user,
    }
    text, _ = Text.objects.get_or_create(uri=resource.get('uri'),  defaults=defaults)
    project.texts.add(text)
    return False
