import requests
import json

class EratosthenesManager(object):
    def __init__(self, endpoint, token):
        if not hasattr(self, 'endpoint'):
            self.endpoint = endpoint

        if not hasattr(self, 'token'):
            self.token = token

    def _handle_status(self, response, status_code):
        pass

    def _get(self, path):
        location = '%s/%s' % (self.endpoint, path)
        response = requests.get(
            location,
            headers={
                'Authorization': 'Token %s' % self.token
            })

        if response.status_code != requests.codes.ok:
            self._handle_status(response, response.status_code)
        try:
            data = json.loads(response.text)
        except ValueError:  # No JSON data.
            data = response.text
        return data

    def repositories(self):
        return self._get('repository')

    def repository(self, id):
        return self._get('repository/%s' % id)

    def collections(self):
        return self._get('collection')

    def collection(self, id):
        return self._get('collection/%s' % id)

    def resources(self):
        return self._get('resource')

    def resource(self, id):
        return self._get('resource/%s' % id)

    def retrieve(self, uri):
        return self._get('retrieve/%s' % uri)

    def resourceContent(self, uri):
        return self._get('content/%s' % uri)
