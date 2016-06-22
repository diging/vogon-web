from repository.models import Repository
from repository.tests.services.simple_json_rest import get, configuration

import unittest


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.repository = Repository.objects.create(
            name = 'Test',
            description = 'describe',
            configuration = configuration
        )

    def test_get_configuration(self):
        self.assertIsInstance(self.repository._get_configuration(), dict)

    def test_methods(self):
        """
        There should be an attribute for each configured method.
        """
        for method in self.repository.configured_methods:
            self.assertTrue(hasattr(self.repository, method))

    def test_get_data_by_path(self):
        path = "path.to.my.data"
        data = {
            'path': {
                'to': {
                    'my': {
                        'data': 42
                    }
                }
            }
        }
        self.assertEqual(42, self.repository._get_data_by_path(data, path))

        path = ""
        data = 42
        self.assertEqual(42, self.repository._get_data_by_path(data, path))

        path = "path"
        data = {
            'path': 42
        }
        self.assertEqual(42, self.repository._get_data_by_path(data, path))

        path = ""
        data = [42, 43, 44, 45]
        self.assertEqual(42, self.repository._get_data_by_path(data, path)[0])

        with self.assertRaises(RuntimeError):
            path = "what.is.this"
            data = {
                'path': {
                    'to': {
                        'my': {
                            'data': 42
                        }
                    }
                }
            }
            self.repository._get_data_by_path(data, path)
