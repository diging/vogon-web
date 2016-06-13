import json
from urlparse import urlparse


class MockResponse(object):
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)


def mock_endpoint(func):
    def handle(request, **params):
        o = urlparse(request)
        status_code, text = func(o, **params)
        return MockResponse(status_code, text)
    return handle
