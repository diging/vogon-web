"""
We should probably write some documentation.
"""

from __future__ import absolute_import

from django.contrib.auth.models import Group
from django.utils.safestring import SafeText
from django.contrib.contenttypes.models import ContentType

import requests
from bs4 import BeautifulSoup
from guardian.shortcuts import assign_perm
import uuid
import re
from itertools import groupby

import slate
from . import managers
from annotations.models import *
from annotations import quadriga

from celery import shared_task


def get_manager(name):
    print dir(managers), name
    try:
        return getattr(managers, name)
    except AttributeError:
        raise ValueError('No such manager.')


def tokenize(content, delimiter=u' '):
    """
    In order to annotate a text, we must first wrap "annotatable" tokens
    in <word></word> tags, with arbitrary IDs.

    Parameters
    ----------
    content : unicode
    delimiter : unicode
        Character or sequence by which to split and join tokens.

    Returns
    -------
    tokenizedContent : unicode
    """
    chunks = content.split(delimiter)
    pattern = u'<word id="{0}">{1}</word>'
    return delimiter.join([pattern.format(i, c) for i, c in enumerate(chunks)])


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
    soup = BeautifulSoup(response.text, "html.parser")

    textData = {
        'title': soup.title.string,
        'content': response.text,
        'content-type': response.headers['content-type'],
    }
    return textData


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
    assign_perm('annotations.view_text', user, text)
    if is_public:
        group = Group.objects.get_or_create(name='Public')[0]
        assign_perm('annotations.view_text', group, text)
    return text





@shared_task
def submit_relationsets_to_quadriga(relationsets, text, user, **kwargs):
    status, response = quadriga.submit_relationsets(relationsets, text, user, **kwargs)
    if status:
        accession = QuadrigaAccession.objects.create(**{
            'createdBy': user,
            'project_id': response.get('project_id'),
            'workspace_id': response.get('workspace_id'),
            'network_id': response.get('networkid')
        })

        for relationset in relationsets:
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


@shared_task
def accession_ready_relationsets():

    qs = RelationSet.objects.filter(submitted=False, pending=False)

    # Do not submit a relationset to Quadriga if the constituent interpretations
    #  involve concepts that are not resolved.
    all_rsets = [rs for rs in qs if rs.ready()]

    print 'processing %i relationsets' % len(all_rsets)
    project_grouper = lambda rs: getattr(rs.occursIn.partOf.first(), 'quadriga_id', -1)

    for project_id, project_group in groupby(sorted(all_rsets, key=project_grouper), key=project_grouper):
        print project_id
        for text_id, text_group in groupby(project_group, key=lambda rs: rs.occursIn.id):
            text = Text.objects.get(pk=text_id)
            for user_id, user_group in groupby(text_group, key=lambda rs: rs.createdBy.id):
                user = VogonUser.objects.get(pk=user_id)
                # We lose the iterator after the first pass, so we want a list here.
                rsets = []
                for rs in user_group:
                    rsets.append(rs)
                    rs.pending = True
                    rs.save()
                kwargs = {}
                if project_id:
                    kwargs.update({
                        'project_id': project_id,
                    })
                submit_relationsets_to_quadriga.delay(rsets, text, user, **kwargs)
