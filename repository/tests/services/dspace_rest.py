"""
Mocks a DSPACE REST API.
"""

from repository.tests.services.base import MockResponse, mock_endpoint

import json, re


def read(o, **kwargs):
    """
    Mock a response to an item request.
    """
    match = re.match('/rest/items/[0-9]+/$', o.path)
    if match:
        with open('repository/tests/services/responses/dspace_item.xml', 'r') as f:
            data = f.read()
    else:
        data = []
    return data


def bitstreams(o, **kwargs):
    """
    Mock a response to a bitstreams request.
    """
    match = re.match('/rest/items/[0-9]+/bitstreams/$', o.path)
    if match:
        with open('repository/tests/services/responses/dspace_item_bitstreams.xml', 'r') as f:
            data = f.read()
    else:
        data = []
    return data


def collections(o, **kwargs):
    """
    Mock a response to a bitstreams request.
    """
    if re.match('/rest/collections/$', o.path):
        with open('repository/tests/services/responses/dspace_collections.xml', 'r') as f:
            data = f.read()
    else:
        data = []
    return data


def collection(o, **kwargs):
    """
    Mock a response to a bitstreams request.
    """
    if re.match('/rest/collections/[0-9]+/items/$', o.path):
        with open('repository/tests/services/responses/dspace_collection_items.xml', 'r') as f:
            data = f.read()
    else:
        data = []
    return data


@mock_endpoint
def get(o, **kwargs):
    status = 200

    if re.match('/rest/items/[0-9]+/$', o.path):
        data = read(o, **kwargs)
    elif re.match('/rest/items/[0-9]+/bitstreams/$', o.path):
        data = bitstreams(o, **kwargs)
    elif re.match('/rest/collections/$', o.path):
        data = collections(o, **kwargs)
    elif re.match('/rest/collections/[0-9]+/items/$', o.path):
        data = collection(o, **kwargs)
    else:
        status = 404
        data = {'body': {'message': 'No such path'}}
    return status, data


configuration = json.dumps({
    'name': 'DSPACE',
    'format': 'xml',
    'description': 'description',
    'endpoint': 'http://localhost:8000/rest/',
    'content_endpoint': 'https://hpsrepository.asu.edu/',
    'namespace': 'https://hpsrepository.asu.edu/handle/',
    'methods': {
        'bitstreams': {
            'name': 'bitstreams',
            'method': 'GET',
            'path': 'items/',
            'request': {
                'template': '{id}/bitstreams/',
            },
            'response': {
                'results': 'list',
                'path': 'bitstreams.bitstream',
                'fields': {
                    'id': {
                        'name': 'id',
                        'type': 'int',
                        'display': 'ID',
                        'path': 'id',
                    },
                    'content_type': {
                        'name': 'content_type',
                        'type': 'text',
                        'display': 'Content type',
                        'path': 'mimeType'
                    },
                    'description': {
                        'name': 'description',
                        'type': 'text',
                        'display': 'Description',
                        'path': 'description'
                    },
                    'name': {
                        'name': 'name',
                        'type': 'text',
                        'display': 'Name',
                        'path': 'name'
                    },
                    'retrieve_link': {
                        'name': 'retrieve_link',
                        'type': 'text',
                        'display': None,
                        'path': 'retrieveLink',
                    },
                    'content_location': {
                        'name': 'content_location',
                        'type': 'template',
                        'display': 'Content location',
                        'template': '{content_endpoint}/{retrieve_link}',
                    }
                },
            }
        },
        'read': {
            'name': 'read',
            'method': 'GET',
            'path': 'items/',
            'request': {
                'template': '{id}/',
            },
            'response': {
                'results': 'instance',
                'path': 'item',
                'fields': {
                    'handle': {
                        'name': 'handle',
                        'display': 'Handle',
                        'type': 'text',
                        'path': 'handle',
                    },
                    'title': {
                        'name': 'title',
                        'display': 'Title',
                        'type': 'text',
                        'path': 'name',
                    },
                    'uri': {
                        'name': 'uri',
                        'display': 'URI',
                        'type': 'url',
                        'template': '{namespace}{handle}',
                    },
                    'updated': {
                        'name': 'updated',
                        'display': 'Last updated',
                        'type': 'datetime',
                        'path': 'lastModified',
                    },
                    'id': {
                        'name': 'id',
                        'display': 'ID',
                        'type': 'int',
                        'path': 'id'
                    }
                },
                'content': {
                    'type': 'bitstream',
                    'method': 'bitstreams'
                }
            }
        },
        'collections': {
            'name': 'collections',
            'method': 'GET',
            'path': 'collections/',
            'request': {},
            'response': {
                'results': 'list',
                'path': 'collections.collection',
                'fields': {
                    'handle': {
                        'name': 'handle',
                        'display': 'Handle',
                        'type': 'text',
                        'path': 'handle',
                    },
                    'name': {
                        'name': 'name',
                        'display': 'Name',
                        'type': 'text',
                        'path': 'name',
                    },
                    'uri': {
                        'name': 'uri',
                        'display': 'URI',
                        'type': 'url',
                        'template': '{namespace}{handle}',
                    },
                    'copyright': {
                        'name': 'copyright',
                        'display': 'Copyright',
                        'type': 'text',
                        'path': 'copyrightText',
                    },
                    'description': {
                        'name': 'description',
                        'display': 'Description',
                        'type': 'text',
                        'path': 'shortDescription',
                    },
                    'id': {
                        'name': 'id',
                        'display': 'ID',
                        'type': 'int',
                        'path': 'id'
                    },
                    'size': {
                        'name': 'size',
                        'display': 'Number of resources',
                        'type': 'int',
                        'path': 'numberItems',
                    },
                },
            }
        },
        'collection': {
            'name': 'collection',
            'method': 'GET',
            'path': 'collections/',
            'request': {
                'template': '{id}/items/'
            },
            'response': {
                'results': 'list',
                'path': 'items.item',
                'fields': {
                    'handle': {
                        'name': 'handle',
                        'display': 'Handle',
                        'type': 'text',
                        'path': 'handle',
                    },
                    'title': {
                        'name': 'title',
                        'display': 'Title',
                        'type': 'text',
                        'path': 'name',
                    },
                    'uri': {
                        'name': 'uri',
                        'display': 'URI',
                        'type': 'url',
                        'template': '{namespace}{handle}',
                    },
                    'updated': {
                        'name': 'updated',
                        'display': 'Last updated',
                        'type': 'datetime',
                        'path': 'lastModified',
                    },
                    'id': {
                        'name': 'id',
                        'display': 'ID',
                        'type': 'int',
                        'path': 'id'
                    }
                },
            }
        },
    }
})
