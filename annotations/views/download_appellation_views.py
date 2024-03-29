from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action, api_view
import csv
from django.shortcuts import render
from django.db.models import Q
from annotations.models import Text, Appellation, CsvDownloadList
from annotations.serializers import CsvDownloadListSerializer
from concepts.models import Concept
import time
from django.core.files import File
import os

@api_view(('POST',))
def export_appellation(request):
    # get text from selected checkboxes
    texts = request.data.get('texts')
    newpath = r'vogon/downloads' 
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    # create temp file in order to save file to db
    temp = 'vogon/downloads/' + str(request.user.id) + '_' + str(int(time.time())) + '.csv' #convert to int first as a shortcut to rounf to whole number
    with open(temp,'w+') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(["String Representation", "Start Position", "End Position", "Concept", "text"])

        for text in texts:
            text_title = Text.objects.get(pk=text).title
            appellations = Appellation.objects.filter(occursIn_id=text)
            for appellation in appellations:
                concept = Concept.objects.get(pk=appellation.interpretation_id)
                try:
                    writer.writerow([appellation.stringRep, appellation.startPos, appellation.endPos, concept.label, text_title])
                except UnicodeEncodeError:
                    # So far this only happend with the label field. Blanketly attaching .encode to all fields causes problems
                    writer.writerow([appellation.stringRep, appellation.startPos, appellation.endPos, concept.label.encode('utf-8'), text_title])
        # save file using file_field
        csv_path_list = CsvDownloadList(user=request.user, file_field=File(csvFile))
        csv_path_list.save()
    # remove temp file
    os.remove(temp)
    # redirect available_csvs
    return Response(status=status.HTTP_200_OK)

@api_view(('GET',))
def available_csvs(request):
    '''
    display list of generated csv that are available for a user to download
    '''
    csv_list = CsvDownloadList.objects.filter(user=request.user.id).order_by('-created')
    serializer = CsvDownloadListSerializer(csv_list, many=True)
    return Response(data=serializer.data)

@api_view(('GET',))
def handle_csv_download(request, download_id):
    csv = CsvDownloadList.objects.get(pk=download_id)
    response = HttpResponse(csv.file_field, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv'
    return response
