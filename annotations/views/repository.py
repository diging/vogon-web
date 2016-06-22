"""
Provides views related to external repositories.
"""

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader

from annotations.forms import RepositorySearchForm
from annotations.models import Repository
from annotations.tasks import tokenize


@login_required
def repository_collections(request, repository_id):
    template = loader.get_template('annotations/repository_collections.html')
    repository = get_object_or_404(Repository, pk=repository_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse collections in %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_collection(request, repository_id, collection_id):
    template = loader.get_template('annotations/repository_collection.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    collection = repository.collection(id=collection_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'collection': collection,
        'title': 'Browse collections in %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_browse(request, repository_id):
    template = loader.get_template('annotations/repository_browse.html')
    repository = get_object_or_404(Repository, pk=repository_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse repository %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_search(request, repository_id):
    template = loader.get_template('annotations/repository_search.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    query = request.GET.get('query', None)
    if query:
        results = repository.search(search=query)
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
    })

    return HttpResponse(template.render(context))


@login_required
def repository_details(request, repository_id):
    template = loader.get_template('annotations/repository_details.html')
    repository = get_object_or_404(Repository, pk=repository_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Repository details: %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_list(request):
    template = loader.get_template('annotations/repository_list.html')
    repositories = Repository.objects.all()

    context = RequestContext(request, {
        'user': request.user,
        'repositories': repositories,
        'title': 'Repositories',

    })

    return HttpResponse(template.render(context))


@login_required
def repository_text(request, repository_id, text_id):
    template = loader.get_template('annotations/repository_text_details.html')

    repository = get_object_or_404(Repository, pk=repository_id)
    result = repository.read(id=int(text_id))

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'result': result,
        'title': 'Text: %s' % result.data['title'].value,

    })
    return HttpResponse(template.render(context))


@login_required
def repository_text_content(request, repository_id, text_id, content_id):
    repository = get_object_or_404(Repository, pk=repository_id)
    result = repository.read(id=int(text_id))
    content = result.content.contents.get(int(content_id))    # Not a dict.
    content_type = content.data.get('content_type', None)
    if content_type and content_type.value == 'text/plain':
        content_response = requests.get(content.data['content_location'].value)
        tokenizedContent = tokenize(content_response.text)
    else:
        return _repository_text_fail(request, repository, result, content)

    defaults = {
        'title': getattr(result.get('title'), 'value', None),
        'created': getattr(result.get('created'), 'value', None),
        #'source': repository,
        'tokenizedContent': tokenizedContent,
        'addedBy': request.user,
        'originalResource': getattr(result.get('url'), 'value', None),
    }
    text, _ = Text.objects.get_or_create(uri=result.uri.value, defaults=defaults)
    return HttpResponseRedirect(reverse('text', args=(text.id,)))


def _repository_text_fail(request, repository, result, content):
    template = loader.get_template('annotations/repository_text_fail.html')

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'result': result,
        'content': content,
        'title': 'Whoops!',
        'content_type': content.data.get('content_type', None),
    })
    return HttpResponse(template.render(context))
