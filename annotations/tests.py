from django.test import TestCase
import unittest
from forms import validatefiletype
from tasks import extract_text_file
from django.core.files import File
from django.core.exceptions import ValidationError


class TestUploadFileType(unittest.TestCase):
    """
    This class tests the validator (to test proper file type - TXT or PDF)
    used in file upload form.
    """
    def test_txt_file(self):
        """
        When file is a TXT file, no exception should be raised.
        """
        f = File('txtfile')
        f.content_type = 'text/plain'
        try:
            validatefiletype(f)
        except ValidationError:
            self.fail('Should not raise Validation Error on a TXT file.')

    def test_pdf_file(self):
        """
        When file is a PDF file, no exception should be raised.
        """
        f = File('pdffile')
        f.content_type = 'application/pdf'
        try:
            validatefiletype(f)
        except ValidationError:
            self.fail('Should not raise Validation Error on a PDF file.')

    def test_invalid_file(self):
        """
        When file is not a zip file, ValidationError should be raised.
        """
        f = File('invalidfile')
        f.content_type = 'invalid'
        with self.assertRaises(ValidationError):
            validatefiletype(f)
