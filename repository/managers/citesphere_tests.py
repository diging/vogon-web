from django.test import TestCase
import unittest.mock as mock
import json

from accounts.models import CitesphereToken, VogonUser
from repository.managers import CitesphereAuthority


class TestCitesphereAuthorityTestCase(TestCase):
    def setUp(self):
        self.user = VogonUser.objects.create(
            username='test',
            password='test',
            email='test@example.com'
        )
        CitesphereToken.objects.create(token='', user=self.user)
        self.citesphere = CitesphereAuthority(
            user=self.user,
            endpoint='https://diging-dev.asu.edu/citesphere-review/api/v1'
        )

    def test_user_info(self):
        user_info = self.citesphere.user_info()
        print(user_info)
