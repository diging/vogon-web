from django.test import TestCase
import unittest.mock as mock
import json

from concepts.viaf import Viaf
from concepts.tests.utils import MockResponse


class ViafSearchTestCase(TestCase):
    def setUp(self):
        self.viaf = Viaf()

    @mock.patch("requests.get")
    def test_empty_concepts(self, mock_get):
        def side_effect(url, params):
            self.assertEqual(params['query'], "nonexistenttopic")
            return MockResponse(json.dumps({
                "query": "nonexistenttopic",
                 "result": None
            }))
        mock_get.side_effect = side_effect

        concepts = self.viaf.search({ 'q': 'nonexistenttopic' })
        self.assertEqual(concepts, [])

    @mock.patch("requests.get")
    def test_multiple_concepts(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/viaf/response_search_multiple.json'
        )

        concepts = self.viaf.search({ 'q': 'einstein' }) 
        expected_concepts = MockResponse.from_file(
            'concepts/tests/viaf/response_search_multiple_expected.json'
        ).json()

        self.assertEqual(concepts, expected_concepts)

class ViafGetTestCase(TestCase):
    def setUp(self):
        self.viaf = Viaf()

    @mock.patch("requests.get")
    def test_concept_with_no_identity(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/viaf/response_get_no_identity.xml'
        )

        concept = self.viaf.get('61634867')
        expected_concept = {
            'concept_type': 'Personal',
            'name': 'Einstein, Alfred, 1880-1952.',
            'identifier': 'http://viaf.org/viaf/61634867',
            'local_identifier': '61634867',
            'identities': []
        }
        self.assertEqual(concept, expected_concept)

    @mock.patch("requests.get")
    def test_concept_with_identities(self, mock_get):
        mock_get.return_value = MockResponse.from_file(
            'concepts/tests/viaf/response_get_with_identities.xml'
        )
        concept = self.viaf.get('61634867')
        expected_concept = {
            'concept_type': 'Personal',
            'name': 'Einstein, Alfred, 1880-1952.',
            'identifier': 'http://viaf.org/viaf/61634867',
            'local_identifier': '61634867',
            'identities': ['ID1', 'ID2', 'ID3', 'ID4']
        }
        self.assertEqual(concept, expected_concept)