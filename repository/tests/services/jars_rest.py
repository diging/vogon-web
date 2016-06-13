"""
Mocks a JARS REST API.
"""

from repository.tests.services.base import MockResponse, mock_endpoint

import json, re


def collections(o, **kwargs):
    """
    Mock a response to a collections request.
    """
    match = re.match('/rest/collection/$', o.path)
    if match:
        with open('repository/tests/services/responses/jars_collections.json', 'r') as f:
            data = json.load(f)
    else:
        data = []
    return data


def collection(o, **kwargs):
    """
    Mock a response to a collection request.
    """
    match = re.match('/rest/collection/([0-9]+)/$', o.path)
    if match:
        with open('repository/tests/services/responses/jars_collection.json', 'r') as f:
            data = json.load(f)
    else:
        data = {"detail":"Not found."}
    return data


def resource(o, **kwargs):
    """
    Mock a response to a resource list request.
    """
    if re.match('/rest/resource/$', o.path):
        with open('repository/tests/services/responses/jars_resources.json', 'r') as f:
            data = json.load(f)
    else:
        data = {"detail":"Not found."}
    return data


def search(o, **kwargs):
    """
    Mock a response to a search request.
    """
    if 'search' in kwargs['params']:
        with open('repository/tests/services/responses/jars_search.json', 'r') as f:
            data = json.load(f)
    else:
        data = {"detail":"Not found."}
    return data


@mock_endpoint
def get(o, **kwargs):
    status = 200

    if re.match('/rest/collection/([0-9]+)/$', o.path):
        data = collection(o, **kwargs)
    elif re.match('/rest/collection/$', o.path):
        data = collections(o, **kwargs)
    elif 'search' in kwargs['params']:
        data = search(o, **kwargs)
    elif re.match('/rest/resource/$', o.path):
        data = resource(o, **kwargs)
    else:
        status = 404
        data = {'body': {'message': 'No such path'}}
    return status, json.dumps(data)


configuration = json.dumps({
    'name': 'JARS',
    'format': 'json',
    'description': 'description',
    'endpoint': 'http://localhost:8000/rest/',
    'methods': {
        'collections': {
            'name': 'collections',
            'method': 'GET',
            'path': 'collection/',
            'request': {},
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': False,
                },
                'path': 'results',
                'fields': {
                    'url': {
                        'name': 'url',
                        'display': 'URL',
                        'type': 'text',
                        'path': 'url',
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
                        'type': 'text',
                        'path': 'uri',
                    },
                    'public': {
                        'name': 'public',
                        'display': 'Public',
                        'type': 'bool',
                        'path': 'public',
                    },
                    'size': {
                        'name': 'size',
                        'display': 'Number of resources',
                        'type': 'int',
                        'path': 'size',
                    },
                    'id': {
                        'name': 'id',
                        'display': 'ID',
                        'type': 'int',
                        'path': 'id',
                    },
                }
            }
        },
        'collection': {
            'name': 'collection',
            'method': 'GET',
            'path': 'collection/',
            'request': {
                'template': '{id}/',
            },
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': False,
                },
                'path': 'resources',
                'fields': {
                    'url': {
                        'name': 'url',
                        'display': 'URL',
                        'type': 'text',
                        'path': 'url',
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
                        'type': 'text',
                        'path': 'uri',
                    },
                    'public': {
                        'name': 'public',
                        'display': 'Public',
                        'type': 'bool',
                        'path': 'public',
                    }
                }
            }
        },
        'list': {
            'name': 'list',
            'method': 'GET',
            'path': 'resource/',
            'request': {},
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': True,
                    'type': 'offset',
                    'max': 'count',
                    'parameter': 'offset',
                },
                'path': 'results',
                'fields': {
                    'url': {
                        'name': 'url',
                        'display': 'URL',
                        'type': 'text',
                        'path': 'url',
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
                        'type': 'text',
                        'path': 'uri',
                    },
                    'public': {
                        'name': 'public',
                        'display': 'Public',
                        'type': 'bool',
                        'path': 'public',
                    }
                }
            }
        },
        'search': {
            'name': 'search',
            'method': 'GET',
            'path': 'resource/',
            'request': {
                'fields': {
                    'search': {
                        'name': 'search',
                        'display': 'Title',
                        'type': 'text',
                    },
                },
            },
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': True,
                    'type': 'offset',
                    'max': 'count',
                    'parameter': 'offset',
                },
                'path': 'results',
                'fields': {
                    'url': {
                        'name': 'url',
                        'display': 'URL',
                        'type': 'text',
                        'path': 'url',
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
                        'type': 'text',
                        'path': 'uri',
                    },
                    'public': {
                        'name': 'public',
                        'display': 'Public',
                        'type': 'bool',
                        'path': 'public',
                    }
                }
            }
        },
    }
})
