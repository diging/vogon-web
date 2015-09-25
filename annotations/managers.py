from django.conf import settings

import requests
from bs4 import BeautifulSoup
import json


class RepositoryManager(object):
    __name__ = 'RepositoryManager'

    def __init__(self, endpoint, **kwargs):
        self.endpoint = endpoint

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return self.__name__

    def collections(self):
        return []

    def collection(self, collection_id):
        return []

    def get(self, uri):
        return {}

    def browse(self):
        return []

    def search(self, query):
        return []

class JARSManager(RepositoryManager):
    __name__ = 'JARS'

    getPattern = '{endpoint}/rest/resource/?uri={uri}'
    getPatternID = '{endpoint}/rest/resource/{id}/'
    browsePattern = '{endpoint}/rest/resource/'
    collectionPattern = '{endpoint}/rest/collection/'
    collectionBrowsePattern = '{endpoint}/rest/collection/{collection}/'
    contentPattern = '{endpoint}{content_location}'
    token = settings.JARS_KEY

    def _cast(self, resource):
        return {
            'title': resource.get('name', None),
            'uri': resource.get('uri', None),
            'id': resource.get('id', None),
            'public': resource.get('public', None)
        }

    def _cast_collection(self, collection):
        return {
            'id': collection.get('id', None),
            'uri': collection.get('uri', None),
            'title': collection.get('name', None),
        }

    def _retrieve(self, remote, allow_redirects=True):
        try:
            response = requests.get(remote, allow_redirects=allow_redirects)
            return json.loads(response.text)
        except Exception as E:
            return self._handle_exception(E)

    def _handle_exception(self, exception):
        if type(exception) is requests.ConnectionError:
            return {}

    def collections(self):
        remote = self.collectionPattern.format(endpoint=self.endpoint)
        jdata = self._retrieve(remote)
        if jdata is None:
            return []
        return [self._cast_collection(c) for c in jdata]

    def collection(self, collection_id):
        remote = self.collectionBrowsePattern.format(
            endpoint=self.endpoint,
            collection=collection_id
        )
        jdata = self._retrieve(remote)['resources']

        if jdata is None:
            return []
        return [self._cast(r) for r in jdata if r['stored']]

    def browse(self):
        remote = self.browsePattern.format(endpoint=self.endpoint)
        jdata = self._retrieve(remote)

        return [self._cast(r) for r in jdata if r['stored']]

    def resource(self, id):
        remote = self.getPatternID.format(endpoint=self.endpoint, id=id)
        jdata = self._retrieve(remote)
        return self._cast(jdata)

    def get(self, uri):
        remote = self.getPattern.format(endpoint=self.endpoint, uri=uri)
        headers = {
            'Authorization': 'Token {token}'.format(token=self.token),
        }
        jdata = self._retrieve(remote)

        remoteContent = self.contentPattern.format(
            endpoint = self.endpoint,
            content_location = jdata['content_location']
        )
        responseContent = requests.get(remoteContent,
                                       allow_redirects=True,
                                       headers=headers)
        if responseContent.status_code != requests.codes.ok:
            raise RuntimeError('Error retrieving resource')

        textData = {
            'title': jdata['name'],
            'content': responseContent.text,
            'content-type': response.headers['content-type'],
        }
        return textData


repositoryManagers = [
    ('JARSManager', 'JARS'),
]
