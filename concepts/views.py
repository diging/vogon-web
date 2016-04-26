from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template import loader
from guardian.shortcuts import get_objects_for_user
from concepts.models import Concept, Type


def list_concept_types(request):
    """
    List all of the concept types
    """
    types = Type.objects.all().values('label', 'description', 'id')
    # types = Concept.objects.exclude(typed__isnull=True).values('typed__label','typed').distinct()

    template = loader.get_template('annotations/concept_types.html')
    context = {
        'types': types,
        'user': request.user,
    }
    return HttpResponse(template.render(context))


def type(request, type_id):
    """
    Fetch description about type
    """
    instance = Type.objects.get(pk=type_id)

    examples  = Concept.objects.filter(typed__id=type_id, concept_state=Concept.RESOLVED).values('id', 'label', 'description')
    template = loader.get_template('annotations/concept_type_detail.html')
    context = {
        'type': instance,
        'user': request.user,
        'examples': examples[:20],
    }
    return HttpResponse(template.render(context))
