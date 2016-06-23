"""
Mocks a simple JSON REST API.
"""

from repository.tests.services.base import MockResponse, mock_endpoint

import json, re


def collections(o, **kwargs):
    """
    Mock a response to a collections request.
    """
    match = re.match('/rest/collections/$', o.path)
    if match:
        data = {
            'body': {
                'collections': [
                    {
                        'id': 1,
                        'name': 'Test collection',
                    },
                    {
                        'id': 2,
                        'name': 'Another collection',
                    },
                ]
            }
        }
    else:
        data = {'body': {'results': []}}
    return data


def collection(o, **kwargs):
    """
    Mock a response to a collection request.
    """
    match = re.match('/rest/collections/([0-9]+)/$', o.path)
    if match:
        data = {
            'body': {
                'results': [
                    {
                        'id': 52,
                        'title': 'The only book with this name',
                    },
                    {
                        'id': 53,
                        'title': 'Another record',
                    },
                ]
            }
        }
    else:
        data = {'body': {'results': []}}
    return data


def search(o, **kwargs):
    """
    Mocks a response to a search request.
    """
    if kwargs['params'].get('title', None) == 'The only book with this name':
        data = {
            'body': {
                'results': [
                    {
                        'id': 52,
                        'title': 'The only book with this name',
                    }
                ]
            }
        }
    else:
        data = {'body': {'results': []}}
    return data


def read(o, **kwargs):
    """
    Mocks a response to a read request.
    """
    match = re.match('/rest/read/([0-9]+)/$', o.path)
    if match:
        data = {
            'body': {
                'content': {
                    'id': 52,
                    'title': 'The only book with this name',
                    'formats': [
                        {
                            'id': 8,
                            'name': 'plain text',
                            'mime': 'text/plain',
                            'location': 'http://testrepository.net/rest/content/0008.txt'
                        },
                        {
                            'id': 9,
                            'name': 'pdf',
                            'mime': 'application/pdf',
                            'location': 'http://testrepository.net/rest/content/0009.txt'
                        },
                    ]
                },
            },
        }
    return data


@mock_endpoint
def get(o, **kwargs):
    status = 200
    if o.path == '/rest/search/':
        data = search(o, **kwargs)
    elif re.match('/rest/read/([0-9]+)/$', o.path):
        data = read(o, **kwargs)
    elif re.match('/rest/collections/([0-9]+)/$', o.path):
        data = collection(o, **kwargs)
    elif re.match('/rest/collections/$', o.path):
        data = collections(o, **kwargs)
    else:
        status = 404
        data = {'body': {'message': 'No such path'}}
    return status, json.dumps(data)


configuration = json.dumps({
    'name': 'Test',
    'format': 'json',
    'description': 'description',
    'endpoint': 'http://testrepository.net/rest/',
    'methods': {
        'read': {
            'name': 'read',
            'method': 'GET',
            'path': 'read/',
            'request': {
                'template': '{id}/',
                'fields': {
                    'id': {
                        'name': 'id',
                        'type': 'int',
                    }
                }
            },
            'response': {
                'path': 'body.content',
                'results': 'instance',
                'content': {
                    'type': 'format',
                    'results': 'list',
                    'path': 'formats',
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
                            'path': 'mime'
                        },
                        'name': {
                            'name': 'name',
                            'type': 'text',
                            'display': 'Name',
                            'path': 'filename'
                        },
                        'content_location': {
                            'name': 'content_location',
                            'type': 'url',
                            'display': 'Content location',
                            'path': 'location',
                        }
                    },
                },
                'fields': {
                    'title': {
                        'name': 'title',
                        'type': 'text',
                        'display': 'Title',
                        'path': 'title',
                    },
                    'id': {
                        'name': 'id',
                        'type': 'int',
                        'display': 'Identifier',
                        'path': 'id',
                    }
                }
            }
        },
        'collections': {
            'name': 'collections',
            'method': 'GET',
            'path': 'collections/',
            'request': {
                'fields': {},
            },
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': False,
                },
                'path': 'body.collections',
                'fields': {
                    'id': {
                        'name': 'id',
                        'display': 'ID',
                        'type': 'int',
                        'path': 'id',
                    },
                    'name': {
                        'name': 'name',
                        'display': 'Name',
                        'type': 'text',
                        'path': 'name',
                    },
                }
            }
        },
        'collection': {
            'name': 'collection',
            'method': 'GET',
            'path': 'collections/',
            'request': {
                'template': '{id}/',
            },
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': False,
                },
                'path': 'body.results',
                'fields': {
                    'title': {
                        'name': 'title',
                        'type': 'text',
                        'display': 'Title',
                        'path': 'title',
                    },
                    'id': {
                        'name': 'id',
                        'type': 'int',
                        'display': 'Identifier',
                        'path': 'id',
                    }
                }
            }
        },
        'search': {
            'name': 'search',
            'method': 'GET',
            'path': 'search/',
            'request': {
                'fields': {
                    'title': {
                        'name': 'title',
                        'display': 'Title',
                        'type': 'text',
                    },
                    'id': {
                        'name': 'id',
                        'type': 'int',
                        'display': 'Identifier',
                        'path': 'id',
                    }
                }
            },
            'response': {
                'results': 'list',
                'pagination': {
                    'paginated': False,
                },
                'path': 'body.results',
                'fields': {
                    'title': {
                        'name': 'title',
                        'type': 'text',
                        'display': 'Title',
                        'path': 'title',
                    },
                    'id': {
                        'name': 'id',
                        'type': 'int',
                        'display': 'Identifier',
                        'path': 'id',
                    }
                }
            }
        }
    }
})
