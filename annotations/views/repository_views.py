"""
Provides views related to external repositories.
"""

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader

from annotations.forms import RepositorySearchForm
from annotations.tasks import tokenize
from repository.models import Repository
from repository.auth import *
from repository.managers import *
from annotations.models import Text, TextCollection

import requests


@login_required
def repository_collections(request, repository_id):
    template = loader.get_template('annotations/repository_collections.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    project_id = request.GET.get('project_id')

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'collections': manager.collections(),
        'title': 'Browse collections in %s' % repository.name,
        'project_id': project_id,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_collection(request, repository_id, collection_id):
    template = loader.get_template('annotations/repository_collection.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    collection = manager.collection(id=collection_id)
    project_id = request.GET.get('project_id')

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'collection': collection,
        'title': 'Browse collections in %s' % repository.name,
        'project_id': project_id,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_browse(request, repository_id):
    template = loader.get_template('annotations/repository_browse.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    project_id = request.GET.get('project_id')
    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'manager': manager,
        'title': 'Browse repository %s' % repository.name,
        'project_id': project_id,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_search(request, repository_id):
    template = loader.get_template('annotations/repository_search.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    query = request.GET.get('query', None)
    project_id = request.GET.get('project_id')
    if query:
        results = manager.search(query=query)
        form = RepositorySearchForm({'query': query})
    else:
        results = None
        form = RepositorySearchForm()

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse repository %s' % repository.name,
        'form': form,
        'results': results,
        'query': query,
        'project_id': project_id,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_details(request, repository_id):
    template = loader.get_template('annotations/repository_details.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    project_id = request.GET.get('project_id')
    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'manager': manager,
        'title': 'Repository details: %s' % repository.name,
        'project_id': project_id,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_list(request):
    template = loader.get_template('annotations/repository_list.html')
    project_id = request.GET.get('project_id')
    context = RequestContext(request, {
        'user': request.user,
        'repositories': Repository.objects.all(),
        'title': 'Repositories',
        'project_id': project_id,

    })

    return HttpResponse(template.render(context))


@login_required
def repository_text(request, repository_id, text_id):
    template = loader.get_template('annotations/repository_text_details.html')
    project_id = request.GET.get('project_id')
    if project_id:
        project = TextCollection.objects.get(pk=project_id)
    else:
        project = None
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    result = manager.resource(id=int(text_id))
    try:
        first_part = result.get('parts')[0]
        serial_content = [{
            'source_id': first_part.get('id'),
            'content_id': content_part['id'],
            'content_type': content_part['content_type']
        } for content_part in first_part['content']]
    except IndexError:
        first_part = None
        serial_content = None


    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'result': result,
        'title': 'Text: %s' % result.get('title'),
        'serial_content': serial_content,
        'project_id': project_id,
        'project': project

    })
    return HttpResponse(template.render(context))


@login_required
def repository_text_content(request, repository_id, text_id, content_id):
    repository = get_object_or_404(Repository, pk=repository_id)

    manager = RepositoryManager(repository.configuration, user=request.user)

    resource = manager.resource(id=int(text_id))
    resource_text_defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': text_id,
        'addedBy': request.user,
    }

    part_of_id = request.GET.get('part_of')
    if part_of_id:
        master = manager.resource(id=int(part_of_id))
        master_resource, _ = Text.objects.get_or_create(uri=master['uri'],
                                                        defaults={
            'title': master.get('title'),
            'created': master.get('created'),
            'repository': repository,
            'repository_source_id': part_of_id,
            'addedBy': request.user,
        })
        resource_text_defaults.update({'part_of': master_resource})

    resource_text, _ = Text.objects.get_or_create(uri=resource['uri'],
                                                  defaults=resource_text_defaults)

    project_id = request.GET.get('project_id')
    if project_id:
        project = TextCollection.objects.get(pk=project_id)
    else:
        project = None

    action = request.GET.get('action', 'annotate')

    # content_resources = {o['id']: o for o in resource['content']}
    # content = content_resources.get(int(content_id))    # Not a dict.
    content = manager.content(id=int(content_id))
    content_type = content.get('content_type', None)

    target, headers = content.get('location'), {}
    # if annotators.annotator_factory()
    # else:
    #     return _repository_text_fail(request, repository, resource, content)

    defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': content_id,
        'addedBy': request.user,
        'content_type': content_type,
        'part_of': resource_text,
        'originalResource': getattr(resource.get('url'), 'value', None),
    }
    text, _ = Text.objects.get_or_create(uri=content['uri'], defaults=defaults)
    if project_id:
        project.texts.add(text.top_level_text)

    if action == 'addtoproject' and project:
        return HttpResponseRedirect(reverse('view_project', args=(project_id,)))
    elif action == 'annotate':
        redirect = reverse('annotate', args=(text.id,))
        if project_id:
            redirect += '?project_id=%s' % str(project_id)
        return HttpResponseRedirect(redirect)



def _repository_text_fail(request, repository, result, content):
    template = loader.get_template('annotations/repository_text_fail.html')
    project_id = request.GET.get('project_id')
    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'result': result,
        'content': content,
        'title': 'Whoops!',
        'content_type': content.get('content_type', None),
        'project_id': project_id,
    })
    return HttpResponse(template.render(context))
