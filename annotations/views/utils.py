from annotations.serializers import TextCollection
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from annotations import annotators
from annotations.models import Text, TextCollection, RelationSet, Appellation
from annotations.serializers import RepositorySerializer, TextSerializer, RelationSetSerializer
from repository.models import Repository
from django.db.models import Q

def get_project_details(request):
    project_id = request.query_params.get('project_id', None)
    if project_id:
        try:
            return TextCollection.objects.get(pk=project_id)
        except TextCollection.DoesNotExist:
            return None
    
    # Return user's default project
    return request.user.get_default_project()

def process_extracted_text(data):
        content = {}
        text_data = data.get('extractedText', None)
        print(text_data)
        if text_data is None:
            return
        text_content_type = text_data.get('content-type')
        text_uri = text_data.get('url')
        content['content_type'] = text_data.get('content-type')
        content['url'] =  text_data.get('url')
        
def _process_additional_files(data):
        additional_files = data.get('additional_files')
        content = {}
        for additional_file in additional_files:
            print(additional_file)
            content_type = additional_file.get('content-type')
            uri = additional_file.get('url')
            resource_type = _get_resource_type(additional_file)
        
# def preprossess_data(data):
#     for item in data:
#         content = process_extracted_text(item)
        
# for item in data[1:]:
#     d = item
#     _process_extracted_text(d)
    
#     break
# #     {
# #                     "url": "https://amphora.asu.edu/amphora/rest/content/11188564/",
# #                     "id": 11188564,
# #                     "uri": "https://diging.asu.edu/geco-giles/files/FILEriSChAzSv3rn",
# #                     "name": "Conway Berners-Lee - Wikipedia.pdf, page 1 (ocr)",
# #                     "public": false,
# #                     "is_external": true,
# #                     "external_source": "GL",
# #                     "content_type": "text/plain",
# #                     "content_for": 11188561
# #                 },
        
      
    #     ''''
    # # data = [
    #         {
    #             "@type": "GilesUpload",
    #             "progressId": "PROGYn023G",
    #             "documentId": "DOCIqLt7BJYw6bQ",
    #             "uploadId": "UPxGwd28LR5BJt",
    #             "uploadedDate": "2021-09-09T06:57:54.853Z",
    #             "uploadedFile": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEr47mULDOhAek",
    #                 "filename": "DigInG-popquiz-2021.docx",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEr47mULDOhAek/content",
    #                 "size": 25170,
    #                 "processor": null,
    #                 "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    #             },
    #             "extractedText": null,
    #             "additionaFiles": null,
    #             "pages": null,
    #             "documentStatus": "COMPLETE",
    #             "uploadingUser": null
    #         },
    #         {
    #             "@type": "GilesUpload",
    #             "progressId": "PROGHEIZgU",
    #             "documentId": "DOCe044bdLHxFfe",
    #             "uploadId": "UPyftKkZr7geHj",
    #             "uploadedDate": "2021-09-09T06:58:37.365Z",
    #             "uploadedFile": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEbGcuhwq8rE9x",
    #                 "filename": "Conway Berners-Lee - Wikipedia.pdf",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEbGcuhwq8rE9x/content",
    #                 "size": 266408,
    #                 "processor": null,
    #                 "content-type": "application/pdf"
    #             },
    #             "extractedText": {
    #                 "@type": "GilesFile",
    #                 "id": "FILE8XGFLTPIydHb",
    #                 "filename": "Conway Berners-Lee - Wikipedia.pdf.txt",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILE8XGFLTPIydHb/content",
    #                 "size": 10873,
    #                 "processor": null,
    #                 "content-type": "text/plain"
    #             },
    #             "additionaFiles": null,
    #             "pages": [
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEMT4owVUkqnVp",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPyftKkZr7geHj%2FDOCe044bdLHxFfe%2FConway+Berners-Lee+-+Wikipedia.pdf.0.tiff",
    #                         "size": 8413323,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEo1lTSylRaojv",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEo1lTSylRaojv/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEdi6mV5ZdO8W4",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEdi6mV5ZdO8W4/content",
    #                         "size": 3413,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEloI7roIdt1P2",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.0.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEloI7roIdt1P2/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILE9AAi4LjsksIA",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILE9AAi4LjsksIA/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEYjYGIqp1eN4T",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPyftKkZr7geHj%2FDOCe044bdLHxFfe%2FConway+Berners-Lee+-+Wikipedia.pdf.1.tiff",
    #                         "size": 2312058,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEgXfOtqYF38tw",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEgXfOtqYF38tw/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEv9vbf2EAKWQu",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEv9vbf2EAKWQu/content",
    #                         "size": 4101,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEQ5ck8qlnK5QV",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.1.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEQ5ck8qlnK5QV/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEBY29oYFPtYgL",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEBY29oYFPtYgL/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEdVV5jBYwodrp",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPyftKkZr7geHj%2FDOCe044bdLHxFfe%2FConway+Berners-Lee+-+Wikipedia.pdf.2.tiff",
    #                         "size": 2073763,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEPlWxit3zfXrN",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEPlWxit3zfXrN/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEMxHcnj2uwUPq",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEMxHcnj2uwUPq/content",
    #                         "size": 3520,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILECblMsB86nIVI",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.2.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILECblMsB86nIVI/content",
    #                             "size": 122,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEWVdw6YzqNdke",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEWVdw6YzqNdke/content",
    #                             "size": 120,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 }
    #             ],
    #             "documentStatus": "COMPLETE",
    #             "uploadingUser": null
    #         },
    #         {
    #             "@type": "GilesUpload",
    #             "progressId": "PROGBpGzj1",
    #             "documentId": "DOCHcmSE7EIJCJ4",
    #             "uploadId": "UPRZtHdNQg0IPP",
    #             "uploadedDate": "2021-08-25T19:10:27.344Z",
    #             "uploadedFile": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEToHx6wG0ZgAB",
    #                 "filename": "dinosaur.txt",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEToHx6wG0ZgAB/content",
    #                 "size": 174499,
    #                 "processor": null,
    #                 "content-type": "text/plain"
    #             },
    #             "extractedText": null,
    #             "additionaFiles": null,
    #             "pages": null,
    #             "documentStatus": "COMPLETE",
    #             "uploadingUser": null
    #         },
    #         {
    #             "@type": "GilesUpload",
    #             "progressId": "PROG1hbitA",
    #             "documentId": "DOCMlsG2T0NtZ1X",
    #             "uploadId": "UPIG1yUdrWKSS4",
    #             "uploadedDate": "2021-09-09T07:00:52.623Z",
    #             "uploadedFile": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEH7o8XBetg1kS",
    #                 "filename": "dinosaur.txt",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEH7o8XBetg1kS/content",
    #                 "size": 174499,
    #                 "processor": null,
    #                 "content-type": "text/plain"
    #             },
    #             "extractedText": null,
    #             "additionaFiles": null,
    #             "pages": null,
    #             "documentStatus": "COMPLETE",
    #             "uploadingUser": null
    #         },
    #         {
    #             "@type": "GilesUpload",
    #             "progressId": "PROGwXnJXw",
    #             "documentId": "DOChqF4nFZObmF2",
    #             "uploadId": "UPzyiAkvarkn3l",
    #             "uploadedDate": "2021-09-13T16:42:22.550Z",
    #             "uploadedFile": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEf9luPPdSarDc",
    #                 "filename": "Conway Berners-Lee - Wikipedia.pdf",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEf9luPPdSarDc/content",
    #                 "size": 266408,
    #                 "processor": null,
    #                 "content-type": "application/pdf"
    #             },
    #             "extractedText": {
    #                 "@type": "GilesFile",
    #                 "id": "FILEu25fMNsyYvq2",
    #                 "filename": "Conway Berners-Lee - Wikipedia.pdf.txt",
    #                 "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEu25fMNsyYvq2/content",
    #                 "size": 10873,
    #                 "processor": null,
    #                 "content-type": "text/plain"
    #             },
    #             "additionaFiles": null,
    #             "pages": [
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEQ6YKLEx3jWCz",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPzyiAkvarkn3l%2FDOChqF4nFZObmF2%2FConway+Berners-Lee+-+Wikipedia.pdf.0.tiff",
    #                         "size": 8413323,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILElHd64SLlEmP2",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILElHd64SLlEmP2/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEapEtSUDAMkhd",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEapEtSUDAMkhd/content",
    #                         "size": 3413,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEgDvGTRGIi7rg",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.0.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEgDvGTRGIi7rg/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEldxO97NlQn4V",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.0.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEldxO97NlQn4V/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEjjFgFevzGdho",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPzyiAkvarkn3l%2FDOChqF4nFZObmF2%2FConway+Berners-Lee+-+Wikipedia.pdf.1.tiff",
    #                         "size": 2312058,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEU54ipsTKhdmq",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEU54ipsTKhdmq/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEGTUUfQFXJLe9",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEGTUUfQFXJLe9/content",
    #                         "size": 4101,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEwSkGR9Mu8tVo",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.1.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEwSkGR9Mu8tVo/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEpSFkO7uZpZMx",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.1.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEpSFkO7uZpZMx/content",
    #                             "size": 25,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "@type": "GilesPage",
    #                     "page": 0,
    #                     "image": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEbCY9QZfOGz0C",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/digilib?fn=images%2FOAUTHCLIENT26_Sudheera%2FUPzyiAkvarkn3l%2FDOChqF4nFZObmF2%2FConway+Berners-Lee+-+Wikipedia.pdf.2.tiff",
    #                         "size": 2073763,
    #                         "processor": null,
    #                         "content-type": "image/tiff"
    #                     },
    #                     "text": {
    #                         "@type": "GilesFile",
    #                         "id": "FILE5gEAahfgYnYP",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILE5gEAahfgYnYP/content",
    #                         "size": 0,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "ocr": {
    #                         "@type": "GilesFile",
    #                         "id": "FILEu6Pb982MF3m9",
    #                         "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff.txt",
    #                         "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEu6Pb982MF3m9/content",
    #                         "size": 3520,
    #                         "processor": null,
    #                         "content-type": "text/plain"
    #                     },
    #                     "additionalFiles": [
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILE1dw6GHkVdmHi",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.2.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILE1dw6GHkVdmHi/content",
    #                             "size": 122,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         },
    #                         {
    #                             "@type": "GilesFile",
    #                             "id": "FILEb86ViM4QalO7",
    #                             "filename": "Conway Berners-Lee - Wikipedia.pdf.2.tiff.txt.species.csv",
    #                             "url": "https://diging.asu.edu/geco-giles-staging/rest/files/FILEb86ViM4QalO7/content",
    #                             "size": 120,
    #                             "processor": "carolus",
    #                             "content-type": "text/csv"
    #                         }
    #                     ]
    #                 }
    #             ],
    #             "documentStatus": "COMPLETE",
    #             "uploadingUser": null
    #         }
    #     ]
    #     '''
@action(detail=True, methods=['post'], url_name='transfertext')
def transfer_to_project(self, request, pk=None, repository_pk=None):
    repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
    manager = repository.manager(request.user)
    result = manager.resource(resource_id=int(pk))
    text = get_object_or_404(Text, uri=result.get('uri'))
    
    try:
        # Retrieve current and target project
        current_project = self._get_project(request, 'project_id')
        target_project = self._get_project(request, 'target_project_id')

        # Transfer text
        self._transfer_text(
            text, current_project, target_project, request.user)
        
        return Response({
            "message": "Successfully transferred text, appellations, and relations"
        })
    except APIException as e:
        return Response({
            "message": e.detail["message"]
        }, e.detail["code"])
    
def _get_project(self, request, field):
    project_id = request.data.get(field, None)
    if not project_id:
        raise APIException({
            "message": f"Could not find `{field}` in request body",
            "code": 400
        })
    try:
        return TextCollection.objects.get(pk=project_id)
    except TextCollection.DoesNotExist:
        raise APIException({
            "message": f"Project with id=`{project_id}` not found!", 
            "code": 404
        })

def _transfer_text(self, text, current_project, target_project, user):
    # Check eligibility
    is_owner = user.pk == current_project.ownedBy.pk
    is_target_contributor = target_project.participants.filter(pk=user.pk).exists()
    is_target_owner = target_project.ownedBy.pk == user.pk
    if not is_owner:
        raise APIException({
            "message": f"User is not the owner of current project '{current_project.name}'",
            "code": 403
        })
    if not (is_target_contributor or is_target_owner):
        raise APIException({
            "message": f"User is not owner/contributor of target project '{target_project.name}'",
            "code": 403
        })

    # Check if text is already part of `target_project`
    if target_project.texts.filter(pk=text.pk).exists():
        raise APIException({
            "message": f"Text `{text.title}` is already part of project `{target_project.name}`!",
            "code": 403
        })

        # Retrieve all related objects for `current_project`
    appellations = Appellation.objects.filter(
        occursIn__in=text.children,
        project=current_project
    )
    relationsets = RelationSet.objects.filter(
        occursIn__in=text.children,
        project=current_project
    )

    with transaction.atomic():
        appellations.update(project=target_project)
        relationsets.update(project=target_project)
        for child in text.children:
            child_text = Text.objects.get(pk=child)
            current_project.texts.remove(child_text)
            target_project.texts.add(child_text)
            
        current_project.save(force_update=True)
        target_project.save(force_update=True)
    
def _get_project_details(self, request, pk):
    project = get_project_details(request)
    if not project:
        return False, None, None

    project_details = ProjectSerializer(project).data
    part_of_project = None
    try:
        project.texts.get(repository_source_id=pk)
        part_of_project = project_details
    except Text.DoesNotExist:
        pass
    return True, project_details, part_of_project
