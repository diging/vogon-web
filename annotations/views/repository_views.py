"""
Provides views related to external repositories.
"""
import requests
from urllib.parse import urlparse, parse_qs
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from annotations.forms import RepositorySearchForm
from annotations.tasks import tokenize
from repository.models import Repository
from repository.auth import *
from repository.managers import *
from annotations.models import Text, TextCollection, RelationSet, VogonUser
from annotations.annotators import supported_content_types
from annotations.serializers import RepositorySerializer, TextSerializer


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        repository = get_object_or_404(queryset, pk=pk)
        manager = RepositoryManager(repository.configuration, user=request.user)
        collections = manager.collections()
        return Response({
            **self.serializer_class(repository).data,
            'collections': collections
        })


class RepositoryCollectionViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = RepositoryManager(repository.configuration, user=request.user)
        collections = manager.collections()
        return Response(collections)

    @action(detail=False, methods=['get'])
    def search(self, request, repository_pk=None):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = RepositoryManager(repository.configuration, user=request.user)
        
        results = manager.search(query=query)
        return Response(results)

    def retrieve(self, request, pk=None, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = RepositoryManager(repository.configuration, user=request.user)
        collection = manager.collection(id=pk)
        return Response(collection)

class RepositoryTextView(viewsets.ViewSet):
    def retrieve(self, request, pk=None, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = RepositoryManager(repository.configuration, user=request.user)
        result = manager.resource(id=int(pk))

        try:
            master_text = Text.objects.get(uri=result.get('uri'))
        except Text.DoesNotExist:
            master_text = None
        aggregate_content = result.get('aggregate_content')
        context = {
            'result': result,
            'master_text': TextSerializer(master_text).data if master_text else None,
        }
        if master_text:
            relations = RelationSet.objects.filter(Q(occursIn=master_text) | Q(occursIn_id__in=master_text.children)).order_by('-created')[:10]
            context['relations'] = relations
        return Response(context)


def _get_params(request):
    # The request may include parameters that should be passed along to the
    #  repository -- at this point, this is just for pagination.
    # TODO: restable should be taking care of this.
    params = request.GET.get('params', {})
    if params:
        params = dict([p.split(':') for p in params.split('|')])

    # Filter resources by the annotators available in this application.
    params.update({'content_type': supported_content_types()})
    return params


def _get_pagination(response, base_url, base_params):
    # TODO: restable should handle pagination, but it seems to be broken right
    #  now. Once that's fixed, we should back off and let restable do the work.
    if not response:
        return None, None
    _next_raw = response.get('next', None)
    if _next_raw:
        _params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v
                   for k, v in list(parse_qs(urlparse(_next_raw).query).items())}
        _next = '|'.join([':'.join(o) for o in list(_params.items())])
        _nparams = {'params': _next}
        _nparams.update(base_params)
        next_page = base_url + '?' + urlencode(_nparams)

    else:
        next_page = None
    _prev_raw = response.get('previous', None)
    if _prev_raw:
        _params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v
                   for k, v in list(parse_qs(urlparse(_prev_raw).query).items())}
        _prev = '|'.join([':'.join(o) for o in list(_params.items())])
        _nparams = {'params': _prev}
        _nparams.update(base_params)
        previous_page = base_url + '?' + urlencode(_nparams)
    else:
        previous_page = None
    return previous_page, next_page



@login_required
def repository_collections(request, repository_id):
    template = "annotations/repository_collections.html"
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    project_id = request.GET.get('project_id')
    try:
        collections = manager.collections()
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)

    context = {
        'user': request.user,
        'repository': repository,
        'collections': collections,
        'title': 'Browse collections in %s' % repository.name,
        'project_id': project_id,
        'manager': manager,
    }

    return render(request, template, context)


@login_required
def repository_collection(request, repository_id, collection_id):
    params = _get_params(request)

    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    try:
        collection = manager.collection(id=collection_id, **params)
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)
    project_id = request.GET.get('project_id')
    base_url = reverse('repository_collection', args=(repository_id, collection_id))
    base_params = {}
    if project_id:
        base_params.update({'project_id': project_id})
    resources = collection.get('resources', [])
    context = {
        'user': request.user,
        'repository': repository,
        'collection': collection,
        'collection_id': collection_id,
        'title': 'Browse collections in %s' % repository.name,
        'project_id': project_id,
        'resources': [resource for resource in resources if resource['url']],
        'subcollections': collection.get('subcollections', [])
    }
    previous_page, next_page = _get_pagination(collection, base_url, base_params)
    if next_page:
        context.update({'next_page': next_page})
    if previous_page:
        context.update({'previous_page': previous_page})
    return render(request, 'annotations/repository_collection.html', context)


@login_required
def repository_browse(request, repository_id):
    params = _get_params(request)

    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    project_id = request.GET.get('project_id')
    try:
        resources = manager.list(**params)
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)

    base_url = reverse('repository_browse', args=(repository_id,))
    base_params = {}
    if project_id:
        base_params.update({'project_id': project_id})


    context = {
        'user': request.user,
        'repository': repository,
        'manager': manager,
        'title': 'Browse repository %s' % repository.name,
        'project_id': project_id,
        'manager': manager,
        'resources': resources['resources'],
    }
    previous_page, next_page = _get_pagination(resources, base_url, base_params)
    if next_page:
        context.update({'next_page': next_page})
    if previous_page:
        context.update({'previous_page': previous_page})

    return render(request, 'annotations/repository_browse.html', context)



@login_required
def repository_search(request, repository_id):
    params = _get_params(request)

    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    query = request.GET.get('query', None)
    project_id = request.GET.get('project_id')
    if query:
        try:
            results = manager.search(query=query, **params)
        except IOError:
            return render(request, 'annotations/repository_ioerror.html', {}, status=500)
        form = RepositorySearchForm({'query': query})
    else:
        results = None
        form = RepositorySearchForm()

    base_url = reverse('repository_search', args=(repository_id))
    base_params = {}
    if project_id:
        base_params.update({'project_id': project_id})
    if query:
        base_params.update({'query': query})

    context = {
        'user': request.user,
        'repository': repository,
        'title': 'Browse repository %s' % repository.name,
        'form': form,
        'results': results,
        'query': query,
        'project_id': project_id,
        'manager': manager,
    }
    previous_page, next_page = _get_pagination(results, base_url, base_params)
    if next_page:
        context.update({'next_page': next_page})
    if previous_page:
        context.update({'previous_page': previous_page})

    return render(request, 'annotations/repository_search.html', context)


def repository_details(request, repository_id):
    from django.contrib.auth.models import AnonymousUser
    template = "annotations/repository_details.html"

    user = None if isinstance(request.user, AnonymousUser) else request.user

    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=user)
    project_id = request.GET.get('project_id')
    context = {
        'user': user,
        'repository': repository,
        'manager': manager,
        'title': 'Repository details: %s' % repository.name,
        'project_id': project_id,
    }

    return render(request, template, context)


@login_required
def repository_list(request):
    template = "annotations/repository_list.html"
    project_id = request.GET.get('project_id')
    context = {
        'user': request.user,
        'repositories': Repository.objects.all(),
        'title': 'Repositories',
        'project_id': project_id,

    }

    return render(request, template, context)


@login_required
def repository_text(request, repository_id, text_id):
    from collections import defaultdict

    project_id = request.GET.get('project_id')
    if project_id:
        project = TextCollection.objects.get(pk=project_id)
    else:
        project = None
    repository = get_object_or_404(Repository, pk=repository_id)
    manager = RepositoryManager(repository.configuration, user=request.user)
    try:
        result = manager.resource(id=int(text_id))
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)

    try:
        master_text = Text.objects.get(uri=result.get('uri'))
    except Text.DoesNotExist:
        master_text = None
    aggregate_content = result.get('aggregate_content')
    serial_content = None
    context = {
        'user': request.user,
        'repository': repository,
        'content': result['content'],
        'result': result,
        'text_id': text_id,
        'title': 'Text: %s' % result.get('title'),
        'serial_content': serial_content,
        'aggregate_content': aggregate_content,
        'project_id': project_id,
        'project': project,
        'master_text': master_text,
    }
    if master_text:
        relations = RelationSet.objects.filter(Q(occursIn=master_text) | Q(occursIn_id__in=master_text.children)).order_by('-created')[:10]
        context.update({
            'relations': relations,
        })

    if project:
        context.update({
            'in_project': master_text and project.texts.filter(pk=master_text.id).exists()
        })
    return render(request, 'annotations/repository_text_details.html', context)


@login_required
def repository_text_content(request, repository_id, text_id, content_id):

    repository = get_object_or_404(Repository, pk=repository_id)

    manager = RepositoryManager(repository.configuration, user=request.user)
    # content_resources = {o['id']: o for o in resource['content']}
    # content = content_resources.get(int(content_id))    # Not a dict.
    try:
        content = manager.content(id=int(content_id))
        resource = manager.resource(id=int(text_id))
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)

    content_type = content.get('content_type', None)
    from annotations import annotators
    if not annotators.annotator_exists(content_type):
        return _repository_text_fail(request, repository, resource, content)
    resource_text_defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': repository,
        'repository_source_id': text_id,
        'addedBy': request.user,
    }
    part_of_id = request.GET.get('part_of')
    if part_of_id:
        try:
            master = manager.resource(id=int(part_of_id))
        except IOError:
            return render(request, 'annotations/repository_ioerror.html', {}, status=500)
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


    target, headers = content.get('location'), {}


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


@login_required
def repository_text_add_to_project(request, repository_id, text_id, project_id):
    repository = get_object_or_404(Repository, pk=repository_id)
    project = get_object_or_404(TextCollection, pk=project_id)

    manager = RepositoryManager(repository.configuration, user=request.user)

    try:
        resource = manager.resource(id=int(text_id))
    except IOError:
        return render(request, 'annotations/repository_ioerror.html', {}, status=500)
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
    return HttpResponseRedirect(reverse('view_project', args=(project_id,)))


def _repository_text_fail(request, repository, result, content):
    template = "annotations/repository_text_fail.html"
    project_id = request.GET.get('project_id')
    context = {
        'user': request.user,
        'repository': repository,
        'result': result,
        'content': content,
        'title': 'Whoops!',
        'content_type': content.get('content_type', None),
        'project_id': project_id,
    }
    return render(request, template, context)
