"""
We should probably write some documentation.
"""

from __future__ import absolute_import

from django.contrib.auth.models import Group
from django.utils.safestring import SafeText
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage



from repository import auth
import requests, uuid, re
from datetime import datetime, timedelta
from django.utils import timezone
from itertools import groupby, chain
from collections import defaultdict

import unicodecsv as csv_unicode
import csv

from annotations.models import *
from annotations import quadriga
from annotations.amphora_utils import retrieve_amphora_text
from annotations.text_upload import repository_text_content, add_text_to_project

from celery import shared_task 

from django.conf import settings

import logging
from itertools import tee

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGLEVEL)



def retrieve(repository, resource):
    """
    Get the content of a resource.

    Parameters
    ----------
    repository : :class:`.Repository`
    resource : unicode or int
        Identifier by which the resource can be retrieved from ``repository``.

    Returns
    -------
    content : unicode
    """
    return repository.getContent(resource)


# TODO: this should be retired.
def scrape(url):
    """
    Retrieve text content from a website.

    Parameters
    ----------
    url : unicode
        Location of web resource.

    Returns
    -------
    textData : dict
        Metadata and text content retrieved from ``url``.
    """
    response = requests.get(uri, allow_redirects=True)

    # TODO : consider plugging in something like DiffBot.
    soup = ""   #BeautifulSoup(response.text, "html.parser")

    textData = {
        'title': soup.title.string,
        'content': response.text,
        'content-type': response.headers['content-type'],
    }
    return textData


# TODO: this should be retired.
def extract_text_file(uploaded_file):
    """
    Extract the text file, and return its content

    Parameters
    ----------
    uploaded_file : InMemoryUploadedFile
        The uploaded text file

    Returns
    -------
    Content of the text file as a string
    """
    if uploaded_file.content_type != 'text/plain':
        raise ValueError('uploaded_file file should be a plain text file')
    filecontent = ''
    for line in uploaded_file:
        filecontent += line + ' '
    return filecontent


# TODO: this should be retired.
def extract_pdf_file(uploaded_file):
    """
    Extract a PDF file and return its content

    Parameters
    ----------
    uploaded_file : InMemoryUploadedFile
        The uploaded PDF file

    Returns
    -------
    Content of the PDF file as a string
    """
    if uploaded_file.content_type != 'application/pdf':
        raise ValueError('uploaded_file file should be a PDF file')
    doc = slate.PDF(uploaded_file)
    filecontent = ''
    for content in doc:
        filecontent += content.decode('utf-8') + '\n\n'
    return filecontent


# TODO: this should be retired.
# TODO: refactor!! This signature stinks.
def save_text_instance(tokenized_content, text_title, date_created, is_public, user, uri=None):
    """
    This method creates and saves the text instance based on the parameters passed

    Parameters
    ----------
    tokenized_content : String
        The tokenized text
    text_title : String
        The title of the text instance
    date_created : Date
        The date to be associated with text instance
    is_public : Boolean
        Whether the text content is public or not
    user : User
        The user who saved the text content
    """
    if not uri:
        uri = 'http://vogonweb.net/' + str(uuid.uuid1())
    text = Text(tokenizedContent=tokenized_content,
            title=text_title,
            created=date_created,
            public=is_public,
            addedBy=user,
            uri=uri)
    text.save()
    if is_public:
        group = Group.objects.get_or_create(name='Public')[0]
    return text



@shared_task
def submit_relationsets_to_quadriga(rset_ids, text_id, user_id, **kwargs):
    logger.debug('Submitting %i relations to Quadriga' % len(rset_ids))
    rsets = RelationSet.objects.filter(pk__in=rset_ids)
    text = Text.objects.get(pk=text_id)
    user = VogonUser.objects.get(pk=user_id)
    status, response = quadriga.submit_relationsets(rsets, text, user, **kwargs)

    if status:
        qsr = RelationSet.objects.filter(pk__in=rset_ids)
        project_id = response.get('projectId')
        workspace_id = response.get('workspaceId')
        network_id = response.get('networkId')
        accession = QuadrigaAccession.objects.create(**{
            'createdBy': user,
            'project_id': project_id,
            'workspace_id': workspace_id,
            'network_id': network_id
        })
        logger.debug('Submitted %i relations as network %s to project %s workspace %s' % (qsr.count(), network_id, project_id, workspace_id))

        for relationset in qsr:
            relationset.submitted = True
            relationset.submittedOn = accession.created
            relationset.submittedWith = accession
            relationset.save()
            for relation in relationset.constituents.all():
                relation.submitted = True
                relation.submittedOn = accession.created
                relation.submittedWith = accession
                relation.save()
            for appellation in relationset.appellations():
                appellation.submitted = True
                appellation.submittedOn = accession.created
                appellation.submittedWith = accession
                appellation.save()
    else:
        logger.debug('Quadriga submission failed with %s' % str(response))

@shared_task
def accession_ready_relationsets():
    logger.debug('Looking for relations to accession to Quadriga...')
    # print 'processing %i relationsets' % len(all_rsets)
    # project_grouper = lambda rs: getattr(rs.occursIn.partOf.first(), 'quadriga_id', -1)

    # for project_id, project_group in groupby(sorted(all_rsets, key=project_grouper), key=project_grouper):
    kwargs = {}

    for project_id in chain([None], TextCollection.objects.values_list('quadriga_id', flat=True).distinct('quadriga_id')):
        if project_id:
            kwargs.update({
                'project_id': project_id,
            })

        qs = RelationSet.objects.filter(submitted=False, pending=False)
        if project_id:
            qs = qs.filter(project_id__quadriga_id=project_id)
        else:    # Don't grab relations that actually do belong to a project.
            qs = qs.filter(project_id__isnull=True)

        # Do not submit a relationset to Quadriga if the constituent interpretations
        #  involve concepts that are not resolved.
        qs = filter(lambda o: o.ready(), qs)
        relationsets = defaultdict(lambda: defaultdict(list))
        for relationset in qs:
            timeCreated = relationset.created
            if timeCreated + timedelta(days=settings.SUBMIT_WAIT_TIME['days'], hours=settings.SUBMIT_WAIT_TIME['hours'], minutes=settings.SUBMIT_WAIT_TIME['minutes']) < datetime.now(timezone.utc):
                relationsets[relationset.occursIn.id][relationset.createdBy.id].append(relationset)
                for text_id, text_rsets in relationsets.iteritems():
                    for user_id, user_rsets in text_rsets.iteritems():
                        # Update state.
                        def _state(obj):
                            obj.pending = True
                            obj.save()
                        map(_state, user_rsets)
                        submit_relationsets_to_quadriga.delay(map(lambda o: o.id, user_rsets), text_id, user_id, **kwargs)


# TODO: this should be retired.
def handle_file_upload(request, form):
    """
    Handle the uploaded file and route it to corresponding handlers

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    form : `django.forms.Form`
        The form with uploaded content

    """
    uploaded_file = request.FILES['filetoupload']
    uri = form.cleaned_data['uri']
    text_title = form.cleaned_data['title']
    date_created = form.cleaned_data['datecreated']
    is_public = form.cleaned_data['ispublic']
    user = request.user
    file_content = None
    if uploaded_file.content_type == 'text/plain':
        file_content = extract_text_file(uploaded_file)
    elif uploaded_file.content_type == 'application/pdf':
        file_content = extract_pdf_file(uploaded_file)

    # Save the content if the above extractors extracted something
    if file_content != None:
        tokenized_content = tokenize(file_content)
        return save_text_instance(tokenized_content, text_title, date_created, is_public, user, uri)


@shared_task
def process_import_task(user, project_id ,file, part_of_id, name):
    try:
        with open(file, 'r') as f:
            csv_file = csv.DictReader(f)
            # there isn't a good way to reset the iterator so we tee them up
            creation_reader, total_count_reader = tee(csv_file)
            creation_reader.next()
            total_count_reader.next()
            total_count = 0
            for row in total_count_reader:
                total_count += 1
            count = 0
            task = ImportTasks.objects.create(
                user = user,
                file_name = name,
                total_rows = int(total_count)
            )
            for row in creation_reader:
                # Store url so we can skip making the request to fetch the json if the urls are the same
                stored_url = ''
                try:
                    parent = Text.objects.get(uri=row["Occurs"])
                    text = Text.objects.get(part_of_id=parent.id)
                    occur = text
                except:
                    # Only make the request and get the json if the url has changed.
                    url = settings.AMPHORA_RESOURCE_URL + row["Occurs"] + "&format=json"
                    if stored_url != url:
                        stored_url = url
                        text_json, text_content = retrieve_amphora_text(url, user)
                    add_text = add_text_to_project(user, 1, text_json['id'],project_id)
                    repo_text_content = repository_text_content(user, 1, text_json['id'], text_content, part_of_id, project_id)
                    if add_text or repo_text_content is False:
                        task = ImportTasks.objects.create(
                                user = user,
                                file_name = name,
                                failed = True
                            )
                        task.save()
                        break
                    text = Text.objects.get(uri=row["Occurs"])
                    occur = Text.objects.get(part_of_id=text.id)
                pos = DocumentPosition.objects.create(
                    position_type = 'CO',
                    position_value = ",".join([row["Start"], row["End"]]),
                    occursIn = occur,
                )
                Appellation.objects.create(
                    stringRep = row["Segment"],
                    startPos = row["Start"],
                    endPos = row["End"],
                    createdBy = user,
                    occursIn = occur,
                    project_id = project_id,
                    interpretation = Concept.objects.get(id=row["Concept"]),
                    position_id = pos.id
                )
                count = count + 1
                task.current_row = int(count)
                task.save()
    except:
        if task:
            task.failed = True
            task.save()
        else:
            task = ImportTasks.objects.create(
                    user = user,
                    file_name = name,
                    failed = True
                )
            task.save()
    default_storage.delete(file)