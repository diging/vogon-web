from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template import loader
from guardian.shortcuts import get_objects_for_user
from concepts.models import Concept


def list_concept_types(request):
    """
    List all of the concept types
    """
    template = loader.get_template('concepts/list_types.html')

    types = Concept.object.all().values('typed__label').distinct()

    paginator = Paginator(types, 15)

    page = request.GET.get('page')
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        texts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        texts = paginator.page(paginator.num_pages)

    context = {
        'types': types,
        'user': request.user,
    }
    return HttpResponse(template.render(context))


def type(request, type_id):
    pass
