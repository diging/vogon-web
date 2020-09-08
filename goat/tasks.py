from __future__ import absolute_import

import os
import urllib
from django.conf import settings
from annotations.models import VogonUser

from goat.models import *


def orchestrate_search(user_id, authority_ids, params):
    """
    Farm out search tasks (in a chord) to each of the :class:`.Authority`
    instances in ``authorities``.
    """
    # We keep track of the parameters so that we don't end up running the same
    #  search several times in a row.
    params_serialized = urllib.parse.urlencode(params)
    user = VogonUser.objects.get(pk=user_id)
    authorities = Authority.objects.filter(pk__in=authority_ids)

    result = [search(user.id, auth.id, params) for auth in authorities]
    return result


def search(user_id, authority_id, params):
    """
    Perform a search using a single :class:`.Authority` instance.

    Parameters
    ----------
    user : :class:`django.contrib.auth.models.User`
    authority : :class:`goat.models.Authority`
    params : dict
    result_id : int
        PK-identifier for :class:`goat.models.SearchResultSet`\.

    Returns
    -------
    concepts : list
        A list of :class:`goat.models.Concept` instances.
    result_id : int
        PK-identifier for :class:`goat.models.SearchResultSet`\.
    """

    user = VogonUser.objects.get(pk=user_id)
    authority = Authority.objects.get(pk=authority_id)
    concepts = []
    results = authority.search(params)
    
    for result in results:
        identities = result.get('identities', None)
        if result['concept_type']:
            try:
                concept_type = Concept.objects.get(identifier=result['concept_type'])
            except Concept.DoesNotExist:
                try:
                    concept_type_result = authority.manager.type(identifier=result['concept_type'])
                except:
                    concept_type_result = None

                defaults = {
                    'added_by': user,
                    'authority': authority
                }
                if concept_type_result:
                    defaults.update({
                        'name': concept_type_result['name'],
                        'local_identifier': result['concept_type'],
                        'description': concept_type_result['description'],

                    })
                else:
                    defaults.update({
                        'name': result['concept_type'],
                        'local_identifier': result['concept_type'],
                    })
                if defaults.get('name') is None:
                    defaults['name'] = result['concept_type']
                concept_type = Concept.objects.create(identifier=result['concept_type'], **defaults)
        else:
            concept_type = None

        concept, _ = Concept.objects.get_or_create(
            identifier=result['identifier'],
            defaults={
                'added_by': user,
                'name': result['name'],
                'local_identifier': result['local_identifier'],
                'description': result['description'],
                'concept_type': concept_type,
                'authority': authority
            }
        )

        if identities:
            _defaults = {
                'added_by': user
            }
            alt_concepts = [
                Concept.objects.get_or_create(
                    identifier=ident,
                    defaults=_defaults)[0]
                for ident in identities
            ]
            identity = Identity.objects.create(
                name = result['name'],
                part_of = authority.builtin_identity_system,
                added_by = user
            )
            identity.concepts.add(concept, *alt_concepts)

        concepts.append(concept)
    return concepts
