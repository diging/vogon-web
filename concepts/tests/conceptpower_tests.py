from django.test import TestCase
import unittest.mock as mock
import json

from concepts.conceptpower import ConceptPower
from concepts.tests.utils import MockResponse


class ConceptPowerSearchTestCase(TestCase):
    def setUp(self):
        self.conceptpower = ConceptPower()
        self.params = {
            'q': 'program',
            'pos': 'noun',
            'limit': 5
        }

    @mock.patch("requests.get")
    def test_empty_concepts(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_empty.xml'
        )
        response = self.conceptpower.search(self.params)
        self.assertEqual(response, [])

    @mock.patch("requests.get")
    def test_single_concept(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_single.xml'
        )
        response = self.conceptpower.search(self.params)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_single_expected.json'
        ).json()
        self.assertEqual(response, expected)

    @mock.patch("requests.get")
    def test_multiple_concepts(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_multiple.xml'
        )
        response = self.conceptpower.search(self.params)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_multiple_expected.json'
        ).json()
        self.assertEqual(response, expected)

    @mock.patch("requests.get")
    def test_all_field_concepts(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_all_field.xml'
        )
        response = self.conceptpower.search(self.params)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_all_field_expected.json'
        ).json()
        self.assertEqual(response, expected)


class ConceptPowerTypeTestCase(TestCase):
    def setUp(self):
        self.conceptpower = ConceptPower()
        self.identifier = 'TYPE_986a7cc9-c0c1-4720-b344-853f08c136ab'
    
    @mock.patch("requests.get")
    def test_empty_type(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_type_empty.xml'
        )
        response = self.conceptpower.type(self.identifier)
        self.assertEqual(response, {})
    
    @mock.patch("requests.get")
    def test_type_all_fields(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_type_all_fields.xml'
        )
        response = self.conceptpower.type(self.identifier)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_type_all_fields_expected.json'
        ).json()
        self.assertEqual(response, expected)

    @mock.patch("requests.get")
    def test_type_with_no_identity(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_type_no_identity.xml'
        )
        response = self.conceptpower.type(self.identifier)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_type_no_identity_expected.json'
        ).json()
        self.assertEqual(response, expected)


class ConceptPowerGetTestCase(TestCase):
    def setUp(self):
        self.conceptpower = ConceptPower()
        self.identifier = 'http://www.digitalhps.org/concepts/WID-07007945-N-01-play'

    @mock.patch("requests.get")
    def test_get_empty(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_empty.xml'
        )
        response = self.conceptpower.get(self.identifier)
        self.assertIsNone(response)

    @mock.patch("requests.get")
    def test_get_concept(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_single.xml'
        )
        response = self.conceptpower.get(self.identifier)
        expected = MockResponse.from_file(
            'concepts/tests/conceptpower/response_search_single_expected.json'
        ).json()[0]
        self.assertEqual(response, expected)


class ConceptPowerCreateTestCase(TestCase):
    def setUp(self):
        self.conceptpower = ConceptPower()
    
    @mock.patch("requests.post")
    def test_create_concept_default(self, mock_post):
        def side_effect(**args):
            data = json.loads(args['data'])
            expected_data = {
                "word": "Test label",
                "pos": "noun",
                "conceptlist": "Test conceptlist",
                "description": "Test",
                "type": "Concept Type",
                "synonymids": [],
                "equals": [],
                "similar": []
            }
            self.assertEqual(data, expected_data)
            return MockResponse("{}")
        
        mock_post.side_effect = side_effect

        response = self.conceptpower.create(
            label='Test label',
            pos='noun',
            conceptlist='Test conceptlist',
            description='Test',
            concept_type='Concept Type'
        )
        self.assertEqual(response, {})

    @mock.patch("requests.post")
    def test_create_concept_all_fields(self, mock_post):
        def side_effect(**args):
            data = json.loads(args['data'])
            expected_data = {
                "word": "Test label",
                "pos": "noun",
                "conceptlist": "Test conceptlist",
                "description": "Test",
                "type": "Concept Type",
                "synonymids": ['id1', 'id2'],
                "equals": ['uri1', 'uri2'],
                "similar": ['uri3', 'uri4']
            }
            self.assertEqual(data, expected_data)
            return MockResponse("{}")

        mock_post.side_effect = side_effect

        response = self.conceptpower.create(
            label='Test label', 
            pos='noun',
            conceptlist='Test conceptlist', 
            description='Test',
            concept_type='Concept Type',
            synonym_ids=['id1', 'id2'],
            equal_uris=['uri1', 'uri2'],
            similar_uris=['uri3', 'uri4']
        )
        self.assertEqual(response, {})

    @mock.patch("requests.post")
    def test_create_concept_error(self, mock_post):
        mock_post.return_value = MockResponse(
            'Error while creating concept',
            status_code=500
        )

        with self.assertRaises(RuntimeError) as context:
            self.conceptpower.create(
                label='Test label', 
                pos='noun',
                conceptlist='Test conceptlist', 
                description='Test',
                concept_type='Concept Type'
            )

        self.assertEqual(500, context.exception.args[0])
        self.assertEqual('Error while creating concept', context.exception.args[1])


