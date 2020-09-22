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
            url=f'{self.endpoint}/user',
            header=self.headers
        )
        return json.loads(response.content)