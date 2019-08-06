"""
Provides network visualization views.
"""

from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse, JsonResponse


from annotations.utils import basepath
from annotations.display_helpers import filter_relationset
from annotations.models import RelationSet, Relation, Appellation, Text
from concepts.models import Concept, Type

from itertools import combinations
from collections import defaultdict, Counter
import copy
# import igraph


def network(request):
    """
    Provides a network browser view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = "annotations/network.html"
    form = None
    context = {
        'baselocation': basepath(request),
        'user': request.user,
        'form': form,
    }
    return render(request, template, context)


def network_for_text(request, text_id):
    """
    Provides network data for the graph tab in the text annotation view.
    """
    relationsets = RelationSet.objects.filter(occursIn_id=text_id)
    appellations = Appellation.objects.filter(asPredicate=False,
                                              occursIn_id=text_id)

    # We may want to show this graph on the public (non-annotation) text view,
    #  and thus want to load appellations created by everyone.
    user_id = request.GET.get('user')
    if user_id:
        relationsets = relationsets.filter(createdBy_id=user_id)
        appellations = appellations.filter(createdBy_id=user_id)
    project_id = request.GET.get('project')
    if project_id:
        relationsets = relationsets.filter(project_id=project_id)
        appellations = appellations.filter(project_id=project_id)
    nodes, edges = generate_network_data_fast(relationsets, text_id=text_id, appellation_queryset=appellations)
    return JsonResponse({'elements': list(nodes.values()) + list(edges.values())})


def generate_network_data_fast(relationsets, text_id=None, user_id=None, appellation_queryset=None):
    """
    Use the :prop:`.RelationSet.terminal_nodes` to build a graph.
    """
    from itertools import groupby, combinations
    if appellation_queryset is None:
        appellation_queryset = Appellation.objects.all()

    nodes = {}
    edges = Counter()
    fields = ['id',
              'terminal_nodes__id',
              'terminal_nodes__label',
              'terminal_nodes__uri',
              'terminal_nodes__typed__id',
              'terminal_nodes__typed__label',
              'terminal_nodes__typed__uri']

    for rset_id, data in groupby(relationsets.values(*fields), key=lambda r: r['id']):
        for source, target in combinations(data, 2):
            edges[tuple(sorted([source['terminal_nodes__id'], target['terminal_nodes__id']]))] += 1.

            for datum in [source, target]:
                if datum['terminal_nodes__id'] in nodes:
                    nodes[datum['terminal_nodes__id']]['data']['weight'] += 1.
                else:
                    appellations = appellation_queryset.filter(interpretation_id=datum['terminal_nodes__id']).values_list('id', flat=True)
                    nodes[datum['terminal_nodes__id']] = {
                        'data': {
                            'id': datum['terminal_nodes__id'],
                            'label': datum['terminal_nodes__label'],
                            'uri': datum['terminal_nodes__uri'],
                            'type': datum['terminal_nodes__typed__id'],
                            'type_label': datum['terminal_nodes__typed__label'],
                            'type_uri': datum['terminal_nodes__typed__uri'],
                            'weight': 1.,
                            'appellations': list(appellations)
                        }
                    }

    edges = {k: {'data': {'weight': v, 'source': k[0], 'target': k[1]}} for k, v in list(edges.items())}

    return nodes, edges


def generate_network_data(relationset_queryset, text_id=None, user_id=None,
                          appellation_queryset=None):
    """
    Generate a network of :class:`.Concept` instances based on
    :class:.`.RelationSet` instances in ``relationset_queryset``.
    """

    # TODO: break this up a bit.

    edges = {}
    nodes = {}
    seen = set([])      # Appellation ids.
    # If we want to show any non-related appellations, we can include them
    #  in this separate appellation_queryset.
    if appellation_queryset:
        # Using select_related gathers all of our database queries related to
        #  this queryset into a single call; this is way more performant than
        #  performing queries each time we access a related field.
        related_fields = ['interpretation', 'interpretation__appellation',
                          'interpretation__appellation__occursIn',
                          'interpretation__typed', 'occursIn']
        appellation_queryset = appellation_queryset.filter(asPredicate=False)\
                                                .select_related(*related_fields)

        # Rather than load whole objects, we only load the fields from the
        #  related models that we actually need. This expands the resultset
        #  quite a bit, because we will get a result object for each target of
        #  the furthest downstream M2M relation (Concept.appellation_set in
        #  this case). But it cuts down our database overhead enormously.
        fields = [
            'interpretation__id',  'interpretation__label',
            'interpretation__uri', 'interpretation__description',
            'interpretation__typed__id', 'id',
            'interpretation__appellation__id',
            'interpretation__appellation__occursIn__id',
            'interpretation__appellation__occursIn__title',
            'interpretation__merged_with__id',
            'interpretation__merged_with__label',
            'interpretation__merged_with__uri',
            'interpretation__merged_with__description',
            'interpretation__merged_with__typed__id',
            'interpretation__merged_with__appellation__id',
            'interpretation__merged_with__appellation__occursIn__id',
            'interpretation__merged_with__appellation__occursIn__title'
        ]

        # This will yield one object per text, so we will see the same
        #  appellation and corresponding interpretations several times.
        for obj in appellation_queryset.values(*fields):
            appell_id = obj.get('id')

            # If the concept used in this appellation has been merged with
            #  another concept, we need to use that master/target concept
            #  instead. In that case, ``merged_with`` will be Truthy. We use
            #  string interpolation below to insert the ``merged_with`` relation
            #  into field lookups. If there is no master/target concept, we will
            #  simply interpolate an empty string.
            if obj.get('interpretation__merged_with__id'):
                mw = 'merged_with__'
            else:
                mw = ''

            # Nodes represent concepts (target of interpretation). We
            #  interpolate ``mw`` in case the concept has been merged.
            node_id = obj.get('interpretation__%sid' % mw)
            node_type = obj.get('interpretation__%styped__id' % mw)
            node_label = obj.get('interpretation__%slabel' % mw)
            node_uri = obj.get('interpretation__%suri' % mw)
            node_description = obj.get('interpretation__%sdescription' % mw)

            if node_id not in nodes:    # Only one node per concept.
                nodes[node_id] = {
                    'data': {
                        'id': node_id,
                        'label': node_label,
                        'uri': node_uri,
                        'description': node_description,
                        'type': node_type,
                        'appellations': set([]),
                        'weight': 1.,
                        'texts': set([])
                    }
                }
            else:   # Don't need to add it again.
                # Node is already in the network, so we just increment weight.
                if appell_id not in seen:   # But only once per appellation.
                    nodes[node_id]['data']['weight'] += 1.
                    seen.add(appell_id)
            # These are useful in the main network view for displaying
            #  information about the texts associated with each concept.
            text_id = obj.get('interpretation__%sappellation__occursIn__id' % mw)
            text_title = obj.get('interpretation__%sappellation__occursIn__title' % mw)

            # We avoid duplicates by using a set; this needs to be recast to
            #  a dict before we return the data.
            nodes[node_id]['data']['texts'].add((text_id, text_title))

            # A set again; must recast to list.
            interp_app_id = obj.get('interpretation__%sappellation__id' % mw)
            nodes[node_id]['data']['appellations'].add(interp_app_id)

    # Rather than load whole objects, we only load the fields from the
    #  related models that we actually need. This expands the resultset
    #  quite a bit, because we will get a result object for each target of
    #  the furthest downstream M2M relation. But it cuts down our database
    #  overhead enormously.
    related_fields = [
        'id', 'occursIn__id', 'occursIn__title',
        'constituents__predicate__interpretation__id',
        'constituents__predicate__interpretation__label',
        'constituents__predicate__interpretation__uri',
        'constituents__predicate__interpretation__description',
        'constituents__predicate__interpretation__merged_with__id',
        'constituents__predicate__interpretation__merged_with__label',
        'constituents__predicate__interpretation__merged_with__uri',
        'constituents__predicate__interpretation__merged_with__description',
        'constituents__source_appellations__id',
        'constituents__object_appellations__id',
        'constituents__source_appellations__asPredicate',
        'constituents__object_appellations__asPredicate',
        'constituents__source_appellations__interpretation__id',
        'constituents__object_appellations__interpretation__id',
        'constituents__source_appellations__interpretation__label',
        'constituents__object_appellations__interpretation__label',
        'constituents__source_appellations__interpretation__uri',
        'constituents__object_appellations__interpretation__uri',
        'constituents__source_appellations__interpretation__description',
        'constituents__object_appellations__interpretation__description',
        'constituents__source_appellations__interpretation__typed__id',
        'constituents__object_appellations__interpretation__typed__id',
        'constituents__source_appellations__interpretation__merged_with__id',
        'constituents__object_appellations__interpretation__merged_with__id',
        'constituents__source_appellations__interpretation__merged_with__label',
        'constituents__object_appellations__interpretation__merged_with__label',
        'constituents__source_appellations__interpretation__merged_with__uri',
        'constituents__object_appellations__interpretation__merged_with__uri',
        'constituents__source_appellations__interpretation__merged_with__description',
        'constituents__object_appellations__interpretation__merged_with__description',
        'constituents__source_appellations__interpretation__merged_with__typed__id',
        'constituents__object_appellations__interpretation__merged_with__typed__id',]

    # We're agnostic about the structure and meaning of the RelationSet, and so
    #  are simply adding edges between any non-predicate concepts that occur
    #  together in a RelationSet. Since we aren't accessing the RelationSet
    #  object directly (only via fields, as described above) we can't get all
    #  of its concepts at once, so we gather them together here in sets. Later
    #  on we iterate over pairs of concepts within each RelationSet using
    #  combinations() to fill in the graph edges.
    relationset_nodes = defaultdict(set)    # Holds Concept (node) ids.

    # Hold on to text ID and title for each RelationSet, so that we can populate
    #  each edge's ``data.texts`` property later on.
    relationset_texts = defaultdict(set)

    # We want to display how each pair of concepts is related. Since we're
    #  agnostic about the structure and meaning of the RelationSet, we simply
    #  gather together all non-generic concepts (i.e. not "be" or "have") used
    #  as "predicates" in the RelationSet. We use the Counter (one per concept)
    #  to keep track of the number of RelationSets that used that predicate for
    #  each pair of concepts.
    relationset_predicates = defaultdict(Counter)

    concept_descriptions = {}   # For ease of access, later.

    # We get one result per constituent Relation in the RelationSet.
    for obj in relationset_queryset.values(*related_fields):
        for field in ['source', 'object']:
            # If the concept used in this appellation has been merged with
            #  another concept, we need to use that master/target concept
            #  instead. In that case, ``merged_with`` will be Truthy. We use
            #  string interpolation below to insert the ``merged_with`` relation
            #  into field lookups.
            if obj.get('constituents__%s_appellations__interpretation__merged_with__id' % field):
                mw = 'merged_with__'
            # If there is no master/target concept, we will simply interpolate
            #  an empty string.
            else:
                mw = ''

            appell_id = obj.get('constituents__%s_appellations__id' % field)
            appell_asPredicate = obj.get('constituents__%s_appellations__asPredicate' % field)
            node_id = obj.get('constituents__%s_appellations__interpretation__%sid' % (field, mw))

            # Node may be a Relation or a DateAppellation, which we don't want
            #  in the network.
            if node_id is None or appell_asPredicate:
                continue

            node_label = obj.get('constituents__%s_appellations__interpretation__%slabel' % (field, mw))
            node_uri = obj.get('constituents__%s_appellations__interpretation__%suri' % (field, mw))
            node_description = obj.get('constituents__%s_appellations__interpretation__%sdescription' % (field, mw))
            node_type = obj.get('constituents__%s_appellations__interpretation__%styped__id' % (field, mw))

            if node_id not in nodes:    # Only one node per concept.
                nodes[node_id] = {
                    'data': {
                        'id': node_id,
                        'label': node_label,
                        'uri': node_uri,
                        'description': node_description,
                        'type': node_type,
                        'appellations': set([]),
                        'weight': 1.,
                        'texts': set([])
                    }
                }
            else:   # Don't need to add it again.
                # Node is already in the network, so we just increment weight.
                if appell_id not in seen:   # But only once per appellation.
                    nodes[node_id]['data']['weight'] += 1.
                    seen.add(appell_id)

            # These are useful in the main network view for displaying
            #  information about the texts associated with each concept.
            text_id = obj.get('occursIn__id')
            text_title = obj.get('occursIn__title')

            # We avoid duplicates by using a set; this needs to be recast to
            #  a dict before we return the data.
            nodes[node_id]['data']['texts'].add((text_id, text_title))

            # A set again; must recast to list.
            interp_app_id = obj.get('constituents__%s_appellations__id' % field)
            nodes[node_id]['data']['appellations'].add(interp_app_id)

        # Check for merged concepts. We'll use string interpolation as before
        #  to select the correct concept.
        #
        # TODO: can we wrap this logic into the block above?
        if obj.get('constituents__source_appellations__interpretation__merged_with__id'):
            source_mw = 'merged_with__'
        else:
            source_mw = ''
        if obj.get('constituents__object_appellations__interpretation__merged_with__id'):
            object_mw = 'merged_with__'
        else:
            object_mw = ''
        if obj.get('constituents__predicate__interpretation__merged_with__id'):
            predicate_mw = 'merged_with__'
        else:
            predicate_mw = ''

        source_id = obj.get('constituents__source_appellations__interpretation__%sid' % source_mw)
        source_asPredicate = obj.get('constituents__source_appellations__asPredicate')
        source_label = obj.get('constituents__source_appellations__interpretation__%slabel' % source_mw)
        source_uri = obj.get('constituents__source_appellations__interpretation__%suri' % source_mw)
        object_id = obj.get('constituents__object_appellations__interpretation__%sid' % object_mw)
        object_asPredicate = obj.get('constituents__object_appellations__asPredicate')
        object_label = obj.get('constituents__object_appellations__interpretation__%slabel' % object_mw)
        object_uri = obj.get('constituents__object_appellations__interpretation__%suri' % object_mw)
        text_id = obj.get('occursIn__id')
        text_title = obj.get('occursIn__title')

        predicate_id = obj.get('constituents__predicate__interpretation__%sid' % predicate_mw)
        predicate_label = obj.get('constituents__predicate__interpretation__%slabel' % predicate_mw)
        predicate_uri = obj.get('constituents__predicate__interpretation__%suri' % predicate_mw)

        relationset_id = obj.get('id')

        if source_id:
            if not source_asPredicate:
                relationset_nodes[relationset_id].add(source_id)
            elif source_uri not in list(settings.PREDICATES.values()):
                concept_descriptions[source_id] = obj.get('constituents__source_appellations__interpretation__%sdescription' % source_mw)
                relationset_predicates[relationset_id][(source_id, source_label)] += 1.

        if object_id:
            if not object_asPredicate:
                relationset_nodes[relationset_id].add(object_id)
            elif object_uri not in list(settings.PREDICATES.values()):
                concept_descriptions[object_id] = obj.get('constituents__object_appellations__interpretation__%sdescription' % object_mw)
                relationset_predicates[relationset_id][(object_id, object_label)] += 1.

        if predicate_id and predicate_uri not in list(settings.PREDICATES.values()):
            concept_descriptions[predicate_id] = obj.get('constituents__predicate__interpretation__%sdescription' % predicate_mw)
            relationset_predicates[relationset_id][(predicate_id, predicate_label)] += 1

        relationset_texts[relationset_id] = (text_id, text_title)

    for relationset_id, relation_nodes in list(relationset_nodes.items()):
        for source_id, object_id in combinations(relation_nodes, 2):
            edge_key = tuple(sorted((source_id, object_id)))
            if edge_key not in edges:
                edges[edge_key] = {
                    'data': {
                        'id': len(edges),
                        'source': source_id,
                        'target': object_id,
                        'weight': 0.,
                        'texts': set([]),
                        'relations': Counter(),
                    }
                }
            edges[edge_key]['data']['texts'].add(relationset_texts[relationset_id])
            for key, value in list(relationset_predicates[relationset_id].items()):
                edges[edge_key]['data']['relations'][key] += value
            edges[edge_key]['data']['weight'] += 1.

    for node in list(nodes.values()):
        node['data']['texts'] = [{'id': text[0], 'title': text[1]}
                                  for text in list(node['data']['texts'])]
        node['data']['appellations'] = list(node['data']['appellations'])

    for edge in list(edges.values()):
        edge['data']['texts'] = [{'id': text[0], 'title': text[1]}
                                  for text in list(edge['data']['texts'])]
        edge['data']['relations'] = [{
            'concept_id': relkey[0],
            'concept_label': relkey[1],
            'count': count,
            'description': concept_descriptions[relkey[0]],
        } for relkey, count in list(edge['data']['relations'].items())]

    return nodes, edges


def network_data(request):
    """
    Generates JSON data for Cytoscape.js graph visualization.
    """
    # project = request.GET.get('project', None)
    # user = request.GET.get('user', None)
    # text = request.GET.get('text', None)

    # TODO: farm some of this out to a utility function (e.g. the igraph bits).

    cache_key = request.get_full_path()
    cache = caches['default']

    response_data = cache.get(cache_key)
    if not response_data:
        queryset = filter_relationset(RelationSet.objects.all(), request.GET)
        # if project:
        #     queryset = queryset.filter(occursIn__partOf_id=project)
        # if user:
        #     queryset = queryset.filter(createdBy_id=user)
        # if text:
        #     queryset = queryset.filter(occursIn_id=text)

        nodes, edges = generate_network_data(queryset)
        nodes_rebased = {}
        edges_rebased = {}
        node_lookup = {}
        max_edge = 0.
        max_node = 0.
        for i, node in enumerate(nodes.values()):
            ogn_id = copy.deepcopy(node['data']['id'])
            nodes_rebased[i] = copy.deepcopy(node)
            # nodes_rebased[i].update({'id': i})
            nodes_rebased[i]['data']['id'] = i
            nodes_rebased[i]['data']['concept_id'] = ogn_id

            node_lookup[ogn_id] = i

            if node['data']['weight'] > max_node:
                max_node = node['data']['weight']
        for i, edge in enumerate(edges.values()):
            ogn_id = copy.deepcopy(edge['data']['id'])
            edges_rebased[i] = copy.deepcopy(edge)

            edges_rebased[i]['data'].update({'id': i + len(nodes_rebased)})
            edges_rebased[i]['data']['source'] = nodes_rebased[node_lookup[edge['data']['source']]]['data']['id']
            edges_rebased[i]['data']['target'] = nodes_rebased[node_lookup[edge['data']['target']]]['data']['id']
            if edge['data']['weight'] > max_edge:
                max_edge = edge['data']['weight']

        for edge in list(edges_rebased.values()):
            edge['data']['weight'] = edge['data']['weight']/max_edge
        for node in list(nodes_rebased.values()):
            node['data']['weight'] = (50 + (2 * node['data']['weight']))/max_node

        graph = igraph.Graph()
        graph.add_vertices(len(nodes_rebased))

        graph.add_edges([(relation['data']['source'], relation['data']['target'])
                         for relation in list(edges_rebased.values())])
        layout = graph.layout_graphopt()
        # layout = graph.layout_fruchterman_reingold(maxiter=500)

        for coords, node in zip(layout._coords, list(nodes_rebased.values())):
            node['data']['pos'] = {
                'x': coords[0] * 5,
                'y': coords[1] * 5
            }

        response_data = {'elements': list(nodes_rebased.values()) + list(edges_rebased.values())}
        cache.set(cache_key, response_data, 300)
    return JsonResponse(response_data)
