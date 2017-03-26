"""
These views provide perspectives on user-created data.
"""

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from annotations.models import Appellation, RelationSet, Text
from annotations.display_helpers import get_snippet_relation, get_snippet
from concepts.models import Concept, Type

from itertools import groupby


def relation_details(request, source_concept_id, target_concept_id):
    """
    Information about :class:`.RelationSet`\s involving a particular pair of
    :class:`.Concept`\s.

    "source" and "target" don't really mean anything here -- there is no
    directionality.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    source_concept_id : int
    target_concept_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    source_concept = get_object_or_404(Concept, pk=source_concept_id)
    target_concept = get_object_or_404(Concept, pk=target_concept_id)

    # Source and target on Relation are now generic, so we need this for lookup.
    appellation_type = ContentType.objects.get_for_model(Appellation)

    source_appellation_ids = Appellation.objects.filter(interpretation=source_concept.id).values_list('id', flat=True)
    target_appellation_ids = Appellation.objects.filter(interpretation=target_concept.id).values_list('id', flat=True)
    q = ((Q(constituents__source_object_id__in=source_appellation_ids) & Q(constituents__source_content_type=appellation_type)) |
         (Q(constituents__object_object_id__in=source_appellation_ids) & Q(constituents__object_content_type=appellation_type)))
    source_queryset = RelationSet.objects.filter(id__in=RelationSet.objects.filter(q).values_list('id', flat=True))

    q = ((Q(constituents__source_object_id__in=target_appellation_ids) & Q(constituents__source_content_type=appellation_type)) |
         (Q(constituents__object_object_id__in=target_appellation_ids) & Q(constituents__object_content_type=appellation_type)))
    combined_queryset = RelationSet.objects.filter(id__in=source_queryset.filter(q).values_list('id', flat=True))

    template = "annotations/relations.html"

    relationsets = []
    for text_id, text_relationsets in groupby(combined_queryset, lambda a: a.occursIn.id):
        text = Text.objects.get(pk=text_id)
        relationsets.append({
            "text_id": text.id,
            "text_title": text.title,
            "relationsets": [{
                "text_snippet": get_snippet_relation(relationset),
                "annotator": relationset.createdBy,
                "created": relationset.created,
            } for relationset in text_relationsets]
        })

    context = {
        'user': request.user,
        'source_concept': source_concept,
        'target_concept': target_concept,
        'relations': relationsets,
    }
    return render(request, template, context)


def concept_details(request, conceptid):
    concept = get_object_or_404(Concept, pk=conceptid)
    appellations = Appellation.objects.filter(interpretation_id=conceptid)

    fields = [
        'id',
        'occursIn_id',
        'occursIn__title',
        'occursIn__tokenizedContent',
        'tokenIds',
        'createdBy_id',
        'createdBy__username',
        'created'
    ]

    appellations = appellations.values(*fields)

    response_format = request.GET.get('format', None)
    response = dict()
    concept_details = []
    appellations_by_text = dict()
    text = ""
    for text_id, text_appellations in groupby(appellations, lambda a: a['occursIn_id']):
        appellation_details = []
        for i, appellation in enumerate(text_appellations):
            if i == 0:
                text_title = appellation['occursIn__title']

            appellation_details.append({
                "text_snippet": get_snippet(appellation),
                "annotator_id": appellation['createdBy_id'],
                "annotator_username": appellation['createdBy__username'],
                "created": appellation['created'],
            })

        concept_details.append({
            "text_id": text_id,
            "text_title": text_title,
            "appellations": appellation_details
        })
    response["texts"] = concept_details
    if response_format == 'json':
        response["concept_label"] = concept.label
        response["concept_uri"] = concept.uri
        response["concept_description"] = concept.description
        return JsonResponse(response)
    else:
        response['concept'] = concept
        template = "{1}"
        context = response
        return render(request, template, context)
