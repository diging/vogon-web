import requests
import json
from django.conf import settings
from rest_framework import status

from accounts.models import CitesphereToken

class CitesphereAuthority:
    def __init__(self, user, endpoint):
        self.endpoint = endpoint
        self.user = user
        self.headers = self._get_auth_header()

    def _get_auth_header(self):
        try:
            self.auth_token = CitesphereToken.objects.get(user=self.user)
            return {'Authorization': f'Bearer {self.auth_token.access_token}'}
        except CitesphereToken.DoesNotExist:
            return {}

    def _get_response(self, endpoint):
        """
        Return response from `endpoint`, 
        get a new token and retry if unauthorized
        """
        response = requests.get(url=endpoint, headers=self.headers)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            self._get_access_token() # Set new token
            return self._get_response(endpoint) # Retry the request
        else:
            return json.loads(response.content)

    def _get_access_token(self):
        """
        Get a new `access_token` using the `refresh_token`
        and save it in `CitesphereToken` object
        """
        refresh_token = self.auth_token.refresh_token
        response = requests.post(
            url=f'{self.endpoint}/api/v1/oauth/token',
            params={
                "client_id": settings.CITESPHERE_CLIENT_ID,
                "client_secret": settings.CITESPHERE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        content = json.loads(response.content)
        self.auth_token.access_token = content["access_token"]
        self.auth_token.save()
        self.headers = self._get_auth_header()

    def user_info(self):
        return self._get_response(f'{self.endpoint}/api/v1/user')

    def collections(self):
        groups = self._get_response(f'{self.endpoint}/api/v1/groups')
        
        # Parse groups to the standard format
        result = []
        for group in groups:
            collection = {
                "id": group['id'],
                "name": group['name'],
                "uri": f"{self.endpoint}/auth/group/{group['id']}",
                "url": f"{self.endpoint}/api/v1/groups/{group['id']}/items",
                "description": group['description'],
                "public": False if group['type'] == "Private" else True,
                "size": group['numItems']
            }
            result.append(collection)

        return result

    def collection(self, col_id, limit=None, offset=None):
        content = self._get_response(f'{self.endpoint}/api/v1/group/{col_id}/items')
        result = {
            "id": col_id,
            "name": content['name'],
            "url": f"{self.endpoint}/api/v1/group/{col_id}/items",
            "public": False if group['type'] == "Private" else True,
        }
        resources = []
        for item in content['items']:
            resources.append({
                "id": item['key'],
                "name": item['title'],
                "title": item['title'],
                "url": "",
                "uri": "",
            })

        result["collections"] = resources
        return result