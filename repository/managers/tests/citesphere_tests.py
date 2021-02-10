from django.test import TestCase
from django.confg import settings
import requests
import unittest.mock as mock
import json

from accounts.models import CitesphereToken, VogonUser
from repository.managers import CitesphereAuthority

from util.test_util import MockResponse


class TestCitesphereAuthorityTestCase(TestCase):
    def setUp(self):
        self.user = VogonUser.objects.create(
            username='test',
            password=settings.TEST_CITESPHERE_PWD,
            email='test@example.com'
        )
        self.token = CitesphereToken.objects.create(
            access_token=settings.TEST_CITESPHERE_ACCESS,
            refresh_token='',
            user=self.user
        )
        self.citesphere = CitesphereAuthority(
            user=self.user,
            endpoint='https://diging-dev.asu.edu/citesphere-review/api/v1'
        )

    @mock.patch("requests.post")
    @mock.patch("requests.get")
    def test_token_expiry_single_retry(self, mock_get, mock_post):
        """
        Tests scenario of access_token expiry
        Expected Flow:
            1. Hit `/api/v1/test` endpoint (citesphere.test_endpoint())
            2. Get 401 error
            3. Get access token
            4. Retry `test_endpoint`
            5. Success Response (200)
        """
        def mock_test_endpoint(url, headers, params):
            if headers["Authorization"] == "Bearer t1":
                # Case 1 - invalid token
                return MockResponse("", status_code=401)
            # Case 2 - valid token
            return MockResponse("{}")

        def mock_refresh_token(url, params):
            return MockResponse(json.dumps({
                "access_token": "t2"
            }))

        mock_get.side_effect = mock_test_endpoint
        mock_post.side_effect = mock_refresh_token

        test_response = self.citesphere.test_endpoint()
        self.assertEqual(test_response, {})

        # `access_token` should be updated to `t2`
        new_token = CitesphereToken.objects.get(user=self.user)
        self.assertEqual(new_token.access_token, "t2")

    @mock.patch("requests.post")
    @mock.patch("requests.get")
    def test_token_invalid_refresh_token(self, mock_get, mock_post):
        """
        Tests scenario of invalid refresh_token
        Expected Flow:
            1. Hit `/api/v1/test` endpoint (citesphere.test_endpoint())
            2. Get 401 error
            3. Try renewing token
            4. Error on renewing token
        """
        def mock_test_endpoint(url, headers, params):
            return MockResponse("", status_code=401)

        def mock_refresh_token(url, params):
            return MockResponse("", status_code=400)

        mock_get.side_effect = mock_test_endpoint
        mock_post.side_effect = mock_refresh_token

        with self.assertRaises(requests.RequestException) as context:
            self.citesphere.test_endpoint()
        
        self.assertEqual("Error renewing access_token", context.exception.args[0])

    @mock.patch("requests.post")
    @mock.patch("requests.get")
    def test_token_max_retry(self, mock_get, mock_post):
        """
        Tests scenario of max retries of access_token
        Expected Flow:
            1. Hit `/api/v1/test` endpoint (citesphere.test_endpoint())
            2. Get 401 error
            3. Renew Token
            4. Repeat 1-3 `retries` times.
            5. Fail request
        """
        def mock_test_endpoint(url, headers, params):
            return MockResponse("", status_code=401)

        def mock_refresh_token(url, params):
            return MockResponse(json.dumps({
                "access_token": "t2"
            }))

        mock_get.side_effect = mock_test_endpoint
        mock_post.side_effect = mock_refresh_token

        with self.assertRaises(requests.exceptions.RetryError) as context:
            self.citesphere.test_endpoint()
        
        self.assertEqual("Could not renew token", context.exception.args[0])

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
        response = self.citesphere.groups()
        self.assertEqual(response, [])

    @mock.patch("requests.get")
    def test_groups_multiple(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'repository/managers/tests/mock_response_collections.json'
        )
        response = self.citesphere.groups()
        expected = MockResponse.from_file(
            'repository/managers/tests/response_collections_expected.json'
        ).json()
        self.assertEqual(response, expected)
