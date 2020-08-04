from itertools import groupby, combinations
from collections import Counter

def network_data(relationsets, text_id=None, appellation_queryset=None):
    """
    Use the :prop:`.RelationSet.terminal_nodes` to build a graph.
    """
    if appellation_queryset is None:
        appellation_queryset = Appellation.objects.all()

    nodes = {}
    edges = Counter()
    fields = [
        'id',
        'terminal_nodes__id',
        'terminal_nodes__label',
        'terminal_nodes__uri',
        'terminal_nodes__typed__id',
        'terminal_nodes__typed__label',
        'terminal_nodes__typed__uri'
    ]
    for rset_id, data in groupby(relationsets.values(*fields), key=lambda r: r['id']):
        for source, target in combinations(data, 2):
            key = tuple(sorted(
                [source['terminal_nodes__id'], target['terminal_nodes__id']]
            ))
            edges[key] += 1.

            for datum in [source, target]:
                if datum['terminal_nodes__id'] in nodes:
                    nodes[datum['terminal_nodes__id']]['data']['weight'] += 1.
                else:
                    appellations = appellation_queryset.filter(
                        interpretation_id=datum['terminal_nodes__id']
                    ).values_list('id', flat=True)
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

    edges = {
        k: {
            'data': {'weight': v, 'source': k[0], 'target': k[1]}
        } for k, v in edges.items()
    }
    return {
        'nodes': nodes.values(),
        'edges': edges.values()
    }

