"""
General-purpose helper functions.
"""

from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from itertools import chain, combinations, groupby
import re
from annotations.models import *
from annotations.relations import create_appellation
from django.shortcuts import get_object_or_404

def help_text(text):
    """
    Remove excess whitespace from a string. Intended for use in model and form
    fields when writing long help_texts.
    """
    return re.sub('(\s+)', ' ', text)

def update_relation(template_part, provided, relationset, cache={}, appellation_cache={}, project_id=None, creator=None, text=None, required=None, _as_key=None):
    relation_cache = get_cache(template_part, cache)
    if relation_cache != None:
        return relation_cache

    field_handlers = get_field_handlers(appellation_cache, project_id, creator, text, required, _as_key)
    relation_data = get_relation_data(relationset, creator, text)

    for pred in ['source', 'predicate', 'object']:    # Collect field data
            node_type = getattr(template_part, '%s_node_type' % pred)
            method = field_handlers.get(node_type, field_handlers['__other__'])
            datum = provided.get((template_part.id, pred))

            dkey = 'predicate' if pred == 'predicate' else '%s_content_object' % pred
            if datum:
                relation_data[dkey] = method(datum)
            elif node_type == RelationTemplatePart.RELATION:
                relation_data[dkey] = update_relation(
                    getattr(template_part, '%s_relationtemplate' % pred), 
                    provided, 
                    relationset, 
                    cache=cache, 
                    appellation_cache=appellation_cache, 
                    project_id=project_id
                )
            else:
                payload = {
                    'type': node_type,
                    'concept_id': getattr(getattr(template_part, '%s_concept' % pred), 'id', None),
                    'part_field': pred
                }
                relation_data[dkey] = create_appellation({}, payload, project_id=project_id, creator=creator, text=text)

    relation_id_q = relationset.constituents.all().values('id')
    relation = get_object_or_404(Relation, pk=relation_id_q[0]['id'])
    relation.source_content_object = relation_data['source_content_object']
    relation.predicate = relation_data['predicate']
    relation.object_content_object = relation_data['object_content_object']
    relation.save()
    
    if cache != None:
        cache[template_part.id] = relation
    return relation

def create_relation(template_part, provided, relationset, cache={}, appellation_cache={}, project_id=None, creator=None, text=None, required=None, _as_key=None):
        relation_cache = get_cache(template_part, cache)
        if relation_cache != None:
            return relation_cache

        field_handlers = get_field_handlers(appellation_cache, project_id, creator, text, required, _as_key)
        relation_data = get_relation_data(relationset, creator, text)

        for pred in ['source', 'predicate', 'object']:    # Collect field data
            node_type = getattr(template_part, '%s_node_type' % pred)
            method = field_handlers.get(node_type, field_handlers['__other__'])
            datum = provided.get((template_part.id, pred))

            dkey = 'predicate' if pred == 'predicate' else '%s_content_object' % pred
            if datum:
                relation_data[dkey] = method(datum)
            elif node_type == RelationTemplatePart.RELATION:
                relation_data[dkey] = create_relation(
                    getattr(template_part, '%s_relationtemplate' % pred), 
                    provided, 
                    relationset, 
                    cache=cache, 
                    appellation_cache=appellation_cache, 
                    project_id=project_id
                )
            else:
                payload = {
                    'type': node_type,
                    'concept_id': getattr(getattr(template_part, '%s_concept' % pred), 'id', None),
                    'part_field': pred
                }
                relation_data[dkey] = create_appellation({}, payload, project_id=project_id, creator=creator, text=text)

        relation = Relation.objects.create(**relation_data)

        if cache != None:
            cache[template_part.id] = relation
        return relation

def get_cache(template_part, cache={}):
    if cache != None:
        key = template_part.id 
        if key in cache:
            return cache[key]
    return None

def get_field_handlers(appellation_cache={}, project_id=None, creator=None, text=None, required=None, _as_key=None):
    field_handlers = {
        RelationTemplatePart.TYPE: lambda datum: Appellation.objects.get(pk=datum['appellation']['id']),
        RelationTemplatePart.DATE: lambda datum: DateAppellation.objects.get(pk=datum['appellation']['id']),
        '__other__': lambda datum: create_appellation(datum, required[_as_key(datum)], cache=appellation_cache, project_id=project_id, creator=creator, text=text)
    }
    return field_handlers

def get_relation_data(relationset, creator=None, text=None):
    relation_data = {
        'part_of': relationset,
        'createdBy': creator,
        'occursIn': text,
    }
    return relation_data

def basepath(request):
    """
    Generate the base path (domain + path) for the site.

    TODO: Do we need this anymore?

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`

    Returns
    -------
    str
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return scheme + request.get_host() + settings.SUBPATH

class VogonAPITestCase(APITestCase):
    def setUp(self):
        from annotations.models import VogonUser
        self.user = VogonUser.objects.create_user(
            "test", "test@example.com", "test", "Test User"
        )
        self.token = RefreshToken.for_user(self.user)
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token.access_token))
