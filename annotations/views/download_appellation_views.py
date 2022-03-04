from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from rest_framework.response import Response
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


@action(detail=True, methods=['post'], url_name='markasread')
def export_appellation_list(request):
	'''
	Display list of texts to download appellations from
	'''
	template = "annotations/export_appellations.html"
	context = {}
	# get texts that are either public or belong to the user and have a content_type of 'text/plain'
	texts = Text.objects.filter((Q(public=True) | Q(addedBy=request.user)) & Q(content_type='text/plain'))
	context['texts'] = texts
	return render(request, template, context)

@action(detail=True, methods=['post'], url_name='markasread')
def export_appellation(request):
	'''
	Create and save csv for future download
	'''

	# get text from selected checkboxes
	texts = request.POST.getlist('texts')

	# create temp file in order to save file to db
	temp = 'vogon/downloads/' + str(request.user.id) + '_' + str(int(time.time())) + '.csv' #convert to int first as a shortcut to rounf to whole number
	with open(temp,'wb+') as csvFile:
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
	return HttpResponseRedirect('/appellations/download/')

@action(detail=True, methods=['post'], url_name='markasread')
def available_csvs(request):
	'''
	display list of generated csv that are available for a user to download
	'''

	csv_list = CsvDownloadList.objects.filter(user=request.user).order_by('-created')
	print(csv_list)
	serializer = CsvDownloadListSerializer(csv_list, many=True)
	return Response(data=serializer.data)

@action(detail=True, methods=['post'], url_name='markasread')
def handle_csv_download(request, download_id):
	'''
	handle the download of the csv
	'''

	csv = CsvDownloadList.objects.get(pk=download_id)
	response = HttpResponse(csv.file_field, content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="export.csv'
	return response
