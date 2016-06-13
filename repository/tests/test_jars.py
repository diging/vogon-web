from repository.models import Repository, Result, ResultSet

import mock, unittest, json

from repository.tests.services.jars_rest import get, configuration


class TestSimpleJsonEndpoint(unittest.TestCase):
    """
    Tests a configuration for a very simple JSON REST API.
    """

    def setUp(self):
        self.repository = Repository.objects.create(
            name = 'JARS',
            description = 'The JARS repository',
            configuration = configuration
        )

    @mock.patch('requests.get', side_effect=get)
    def test_collections(self, mock_effect):
        results = self.repository.collections()

        self.assertIsInstance(results, ResultSet)
        self.assertEqual(results.count, 1)
        self.assertIsInstance(results[0], Result)
        self.assertTrue(hasattr(results[0], 'name'))

    @mock.patch('requests.get', side_effect=get)
    def test_collection(self, mock_effect):
        results = self.repository.collection(id=1)

        self.assertIsInstance(results, ResultSet)
        self.assertEqual(results.count, 20)
        self.assertIsInstance(results[0], Result)
        self.assertTrue(hasattr(results[0], 'title'))

    @mock.patch('requests.get', side_effect=get)
    def test_list(self, mock_effect):
        results = self.repository.list()

        self.assertIsInstance(results, ResultSet)
        self.assertEqual(results.count, 10)
        self.assertIsInstance(results[0], Result)
        self.assertTrue(hasattr(results[0], 'title'))


    @mock.patch('requests.get', side_effect=get)
    def test_search(self, mock_effect):
        results = self.repository.search(search='danio')

        self.assertIsInstance(results, ResultSet)
        self.assertEqual(results.count, 4)
        self.assertIsInstance(results[0], Result)
        self.assertTrue(hasattr(results[0], 'title'))
