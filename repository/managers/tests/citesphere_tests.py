from django.test import TestCase
import unittest.mock as mock
import json

from accounts.models import CitesphereToken, VogonUser
from repository.managers import CitesphereAuthority

from util.test_util import MockResponse


class TestCitesphereAuthorityTestCase(TestCase):
    def setUp(self):
        self.user = VogonUser.objects.create(
            username='test',
            password='test',
            email='test@example.com'
        )
        CitesphereToken.objects.create(
            access_token='',
            refresh_token='',
            user=self.user
        )
        self.citesphere = CitesphereAuthority(
            user=self.user,
            endpoint='https://diging-dev.asu.edu/citesphere-review/api/v1'
        )

    def test_token_expiry(self):
        pass

    @mock.patch("requests.get")
    def test_user_info(self, mock_get):
        user_info_mock = {
            "username": "test",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User"
        }
        mock_get.return_value = MockResponse(json.dumps(user_info_mock))
        user_info = self.citesphere.user_info()
        self.assertEqual(user_info, user_info_mock)

    @mock.patch("requests.get")
    def test_groups_empty(self, mock_get):
        mock_get.return_value = MockResponse(json.dumps([]))
        response = self.citesphere.collections()
        self.assertEqual(response, [])

    @mock.patch("requests.get")
    def test_groups_multiple(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'repository/managers/tests/mock_response_collections.json'
        )
        response = self.citesphere.collections()
        expected = MockResponse.from_file(
            'repository/managers/tests/response_collections_expected.json'
        ).json()
        self.assertEqual(response, expected)

