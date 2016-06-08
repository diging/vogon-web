from django.test import TestCase
import unittest
from annotations.forms import validatefiletype
from annotations.tasks import extract_text_file, extract_pdf_file
from django.core.files import File
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


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

    # def test_pdf_file(self):
    #     """
    #     When file is a PDF file, no exception should be raised.
    #     """
    #     f = File('pdffile')
    #     f.content_type = 'application/pdf'
    #     try:
    #         validatefiletype(f)
    #     except ValidationError:
    #         self.fail('Should not raise Validation Error on a PDF file.')

    def test_invalid_file(self):
        """
        When file is not a zip file, ValidationError should be raised.
        """
        f = File('invalidfile')
        f.content_type = 'invalid'
        with self.assertRaises(ValidationError):
            validatefiletype(f)


# Disabling these for now, since we are disallowing PDFs at the moment.

# class TestPDFFileExtract(unittest.TestCase):
#     """
#     This class tests the PDF file extraction method after upload file form
#     is submitted.
#     """
#
#     def test_not_a_pdf_file(self):
#         """
#         This method tests if validation error is raised when a non-PDF file is
#         uploaded
#         """
#         f = File('invalid')
#         f.content_type = 'invalid'
#         with self.assertRaises(ValueError):
#             extract_pdf_file(f)
#
#     def test_pdf_file(self):
#         """
#         This method tests if contents of the PDF file are extracted when a PDF
#         file is uploaded.
#         """
#         with open('annotations/tests/data/test.pdf', 'r') as f:
#             pdf = File(f)
#             pdf.content_type = 'application/pdf'
#             content = extract_pdf_file(pdf)
#             self.assertEquals(content.strip(), 'This is a sample test file.')


class TestTextFileExtract(unittest.TestCase):
    """
    This class tests the text file extraction method after the upload file
    form is submitted.
    """

    def test_not_a_txt_file(self):
        """
        This method tests if validation error is raised when a non-text file is
        uploaded
        """
        f = File('invalid')
        f.content_type = 'invalid'
        with self.assertRaises(ValueError):
            extract_text_file(f)

    def test_text_file(self):
        """
        This method tests if content of the text file are extracted when
        a text file is uploaded
        """
        f = ContentFile('This is a sample content', name='test.txt')
        f.content_type = 'text/plain'
        content = extract_text_file(f)
        self.assertEquals(content.strip(), 'This is a sample content')



class TextQuadrigaSerialization(unittest.TestCase):
    pass
