import requests
import json
from django.conf import settings
from rest_framework import status

from accounts.models import CitesphereToken

class CitesphereAuthority:
    def __init__(self, user):
        self.user = user
        self.headers = self._get_auth_header()

    def test_endpoint(self):
        return self._get_response(f'{settings.CITESPHERE_ENDPOINT}/api/v1/test')

    def user_info(self):
        return self._get_response(f'{settings.CITESPHERE_ENDPOINT}/api/v1/user')

    def groups(self):
        groups = self._get_response(f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups')
        return list(map(self._parse_group_info, groups))

    def group_info(self, group_id):
        group = self._get_response(f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}')
        return self._parse_group_info(group)

    def group_items(self, group_id, page=1):
        params = { "page": page }
        response = self._get_response(
            f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}/items',
            params=params
        )
        return response
        
    def group_item(self, group_id, item_id):
        response = self._get_response(
            f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}/items/{item_id}'
        )
        return response
        
    def content(self, file_id):
        return self._get_response(f'{settings.GILES_FILE_ENDPOINT}/{file_id}/content')

    def group_collections(self, group_id, limit=None, offset=None):
        return self._get_response(f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}/collections')

    def collection_items(self, group_id, col_id, page=1):
        params = { "page": page }
        return self._get_response(
            f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}/collections/{col_id}/items',
            params=params
        )

    def collection_collections(self, group_id, col_id):
        return self._get_response(
            f'{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group_id}/collections/{col_id}/collections'
        )
    
    def _get_auth_header(self):
        try:
            self.auth_token = CitesphereToken.objects.get(user=self.user)
            return {'Authorization': f'Bearer {self.auth_token.access_token}'}
        except CitesphereToken.DoesNotExist:
            return {}

    def _get_response(self, endpoint, params = None):
        """
        Return response from `endpoint`,
        get a new token and retry if unauthorized
        """
        retries = 5
        for _ in range(retries):
            response = requests.get(url=endpoint, headers=self.headers, params=params)
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                try:
                    self._get_access_token() # Set new token
                except requests.RequestException as e:
                    raise e
            elif response.status_code == status.HTTP_200_OK:
                try:
                    data = json.loads(response.content)
                except Exception as e:
                    data = response.content
                return data
            elif response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR]:
                return "error", response.status_code

        raise requests.exceptions.RetryError("Could not renew token")

    def _get_access_token(self):
        """
        Get a new `access_token` using the `refresh_token`
        and save it in `CitesphereToken` object
        """
        refresh_token = self.auth_token.refresh_token
        response = requests.post(
            url=f'{settings.CITESPHERE_ENDPOINT}/api/oauth/token',
            params={
                "client_id": settings.CITESPHERE_CLIENT_ID,
                "client_secret": settings.CITESPHERE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        if response.status_code == 200:
            content = json.loads(response.content)
            self.auth_token.access_token = content["access_token"]
            self.auth_token.save()
            self.headers = self._get_auth_header()
        else:
            raise requests.RequestException("Error renewing access_token")

    def _parse_group_info(self, group):
        return {
            "id": group['id'],
            "name": group['name'],
            "uri": f"{settings.CITESPHERE_ENDPOINT}/api/v1/auth/group/{group['id']}",
            "url": f"{settings.CITESPHERE_ENDPOINT}/api/v1/groups/{group['id']}/items",
            "description": group['description'],
            "public": False if group['type'] == "Private" else True,
            "size": group['numItems']
        }
    
    def get_raw(self, target, **params):
        return requests.get(
            url=target,
            headers=self.headers,
            params=params
        ).content