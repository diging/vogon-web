import unittest
from annotations.utils import help_text


class TestHelpText(unittest.TestCase):
    def test_help_text(self):
        text = u"\n\n\nThis  sentence has \n\nstrange whitespace"
        expectation = u"This sentence has strange whitespace"
        self.assertEquals(expectation, help_text(expectation))
