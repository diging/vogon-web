import requests
import json

from accounts.models import GithubToken

class AmphoraRepository:
    def __init__(self, user, endpoint):
        self.endpoint = endpoint
        self.user = user
        self.headers = {
            **self._get_auth_header()
        }

    def _get_auth_header(self):
        try:
            auth_token = GithubToken.objects.get(user=self.user)
            return {'Authorization': f'GithubToken {auth_token.token}'}
        except GithubToken.DoesNotExist:
            return {}

    def resources(self, limit=None, offset=None):
        response = requests.get(
            url=f'{self.endpoint}/resource/',
            headers=self.headers,
            params={'limit': limit, 'offset': offset}
        )
        return json.loads(response.content)
        
    def resource(self, id):
        response = requests.get(
            url=f'{self.endpoint}/resource/{id}/',
            headers=self.headers
        )
        result = json.loads(response.content)
        content = [
            {
                'name': x.get('content_resource').get('name', ''),
                'id': x.get('content_resource').get('id'),
                'content_type': x.get('content_resource').get('content_type', ''),
                'source': x.get('content_resource').get('external_source', '')
            }
            for x in result.get('content', [])
        ]
        result['title'] = result['name']
        result['content'] = content
        return result

    def collections(self):
        response = requests.get(
            url=f'{self.endpoint}/collection/',
            headers=self.headers
        )
        return json.loads(response.content).get('results', [])

    def collection(self, id, limit=None, offset=None):
        response = requests.get(
            url=f'{self.endpoint}/collection/{id}/',
            headers=self.headers,
            params={'limit': limit, 'offset': offset}
        )
        content = json.loads(response.content)
        resources = [
            {
                **x,
                'title': x.get('name', '')
            } 
            for x in content.get('resources', {}).get('results', [])
        ]
        content['resources'] = resources
        return content

    def search(self, query, limit=None, offset=None):
        response = requests.get(
            url=f'{self.endpoint}/resource/',
            headers=self.headers,
            params={'limit': limit, 'offset': offset, 'search': query}
        )
        return json.loads(response.content)

    def content(self, id):
        response = requests.get(
            url=f'{self.endpoint}/content/{id}/',
            headers=self.headers,
        )
        result = json.loads(response.content)
        if not result.get('content_location', None):
            return None
        result['location'] = result['content_location']
        result['title'] = result['name']
        
        next_resource = result['next'].get('resource', {})
        next_content = result['next'].get('content', [])
        previous_resource = result['previous'].get('resource', {})
        previous_content = result['previous'].get('content')
        result['next'] = next_resource
        result['next_content'] = next_content
        result['previous'] = previous_resource
        result['previous_content'] = previous_content

        return result

    def get_raw(self, target, **params):
        return requests.get(
            url=target,
            headers=self.headers,
            params=params
        ).content