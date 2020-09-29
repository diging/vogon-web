import requests
import json

from accounts.models import CitesphereToken

class CitesphereAuthority:
    def __init__(self, user, endpoint):
        self.endpoint = endpoint
        self.user = user
        self.headers = {
            **self._get_auth_header()
        }

    def _get_auth_header(self):
        try:
            auth_token = CitesphereToken.objects.get(user=self.user)
            return {'Authorization': f'Bearer {auth_token.token}'}
        except CitesphereToken.DoesNotExist:
            return {}

    def user_info(self):
        response = requests.get(
            url=f'{self.endpoint}/api/v1/user',
            headers=self.headers
        )
        return json.loads(response.content)

    def collections(self):
        response = requests.get(
            url=f'{self.endpoint}/api/v1/groups',
            headers=self.headers
        )
        groups = json.loads(response.content)
        
        # Parse groups to the standard format
        result = []
        for group in groups:
            collection = {
                "id": group['id'],
                "name": group['name'],
                "uri": f"{self.endpoint}/auth/group/{group['id']}",
                "url": f"{self.endpoint}/api/v1/groups/{group['id']}/items",
                "description": group['description'],
                "public": False if group['type'] == "Private" else True
            }
            result.append(group)

        return result

    def collection(self, id, limit=None, offset=None):
        response = requests.get(
            url=f'{self.endpoint}/api/v1/group/{id}/items'
        )
        content = json.loads(response.content)
        result = {
            "id": id,
            "name": content['name'],
            "url": f"{self.endpoint}/api/v1/group/{id}/items",
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