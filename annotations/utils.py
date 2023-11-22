"""
General-purpose helper functions.
"""

from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from itertools import chain, combinations, groupby
from annotations.models import *

def basepath(request):
    """
    Generate the base path (domain + path) for the site.

    TODO: Do we need this anymore?

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`

    Returns
    -------
    str
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return scheme + request.get_host() + settings.SUBPATH

class VogonAPITestCase(APITestCase):
    def setUp(self):
        from annotations.models import VogonUser
        self.user = VogonUser.objects.create_user(
            "test", "test@example.com", "test", "Test User"
        )
        self.token = RefreshToken.for_user(self.user)
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token.access_token))
