from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template import loader
from guardian.shortcuts import get_objects_for_user
from concepts.models import Concept


def list_concept_types(request):
    """
    List all of the concept types
    """
    types = Concept.objects.exclude(typed__isnull=True).values('typed__label','typed').distinct()


    context = {
        'types': types,
        'user': request.user,
    }
    return HttpResponse(str(context))#template.render(context))


def type(request, type_id):
    pass
