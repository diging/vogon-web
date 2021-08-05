from functools import reduce
from itertools import groupby
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache

from goat import tasks
from goat.serializers import *
from goat.models import *

def get_concept_cache_key(query, pos):
    if not pos:
        return query
    return f"{pos}###{query}"

def search(*args, **kwargs):
    """
    Trigger a search
    """
    q = kwargs.get('q', None)
    if not q:
        return []

    params = {k: v[0] if isinstance(v, list) else v
              for k, v in kwargs.items()}

    # The client can coerce a new search even if we have results for an
    #  identical query.
    force = params.pop('force', None) == 'force'
    cache_key = get_concept_cache_key(q, kwargs.get("pos"))
    if not force and cache.get(cache_key):
        return cache.get(cache_key)

    # We let the asynchronous task create the SearchResultSet, since it will
    #  spawn tasks that need to update the SearchResultSet upon completion.
    result = tasks.orchestrate_search(kwargs['user_id'], list(Authority.objects.all().values_list('id', flat=True)),
                                            params)

    # We have to build this manually, since the SearchResultSet probably does
    #  not yet exist.
    result = reduce(lambda x,y: x+y, result) # Flatten
    result = ConceptSerializer(result, many=True).data
    cache.set(cache_key, result, 24 * 60 * 60) # Set 24hrs expiry
    return result

def retrieve(identifier):
    """
    Get a :class:`.Concept` by identifier.
    """
    concept = get_object_or_404(Concept, identifier=identifier)
    serialized = ConceptSerializer(concept).data
    return serialized

def identical(identifier, system_id=None):
    """
    This provides a simpler view onto :class:`.Identity` instances than the
    :class:`.IdentityViewSet`\. Here the client can pass an identifier and
    (optionally) an ID for a :class:`.IdentitySystem` instance, and get an
    array of identical :class:`.Concept`\s.
    """

    concept = get_object_or_404(Concept, identifier=identifier)

    identities = concept.identities.all()

    if system_id:
        identities = identities.filter(part_of_id=system_id)
    try:    # The QuerySet is lazy, so we do the serialization in here.
        concepts = Concept.objects.filter(identities__in=identities.values_list('id', flat=True)).distinct('id')
        serialized = ConceptSerializer(concepts, many=True).data
    except:    # This is kind of a drag, but SQLite doesn't support DISTINCT ON.
        concepts = Concept.objects.filter(identities__in=identities.values_list('id', flat=True))
        concepts = [[c for c in concept][0] for i, concept in groupby(sorted(concepts, key=lambda o: o.id), key=lambda o: o.id)]
        serialized = ConceptSerializer(concepts, many=True).data

    return serialized