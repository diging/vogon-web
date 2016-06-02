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


def save_text_instance(tokenized_content, text_title, date_created, is_public, user):
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
    uniqueuri = 'http://vogonweb.net/' + str(uuid.uuid1())
    text = Text(tokenizedContent=tokenized_content,
            title=text_title,
            created=date_created,
            public=is_public,
            addedBy=user,
            uri=uniqueuri)
    text.save()
    assign_perm('annotations.view_text', user, text)
    if is_public:
        group = Group.objects.get_or_create(name='Public')[0]
        assign_perm('annotations.view_text', group, text)
    return text


def get_snippet_relation(relationset):
    """
    Get a text snippet for a :class:`.RelationSet` instance.
    """

    appellation_type = ContentType.objects.get_for_model(Appellation)
    tokenizedContent = relationset.occursIn.tokenizedContent
    annotated_words = []

    # We'll use this to label highlighted tokens with their interpretations.
    annotation_map = {}

    fields = [
        'source_content_type_id',
        'object_content_type_id',
        'source_object_id',
        'object_object_id',
        'predicate__tokenIds',
        'predicate__interpretation__label',
        'predicate__interpretation_id',
    ]

    appellation_ids = set()

    # Pull out all Appellations that have a specific textual basis.
    for relation in relationset.constituents.values(*fields):
        for part in ['source', 'object']:
            if relation.get('%s_content_type_id' % part, None) == appellation_type.id:
                appellation_ids.add(relation['%s_object_id' % part])

        # Predicates too, since we're interested in evidence for the relation.
        if relation['predicate__tokenIds']:
            tokenIds = relation['predicate__tokenIds'].split(',')
            annotated_words.append(tokenIds)
            for t in tokenIds:
                annotation_map[t] = relation['predicate__interpretation__label']

    appellation_fields = [
        'tokenIds',
        'interpretation__label',
        'interpretation_id',
        'interpretation__merged_with_id',
        'interpretation__merged_with__label',
    ]
    for appellation in Appellation.objects.filter(pk__in=appellation_ids).values(*appellation_fields):

        tokenIds = appellation['tokenIds'].split(',')
        annotated_words.append(tokenIds)
        for t in tokenIds:
            if appellation['interpretation__merged_with_id']:
                annotation_map[t] = appellation['interpretation__merged_with__label']
            else:
                annotation_map[t] = appellation['interpretation__label']

    # Group sequences of tokens from appellations together if they are in close
    #  proximity.
    grouped_words = []
    for tokenSeq in sorted(annotated_words, key=lambda s: min([int(t) for t in s])):
        tokenSeqI = [int(t) for t in tokenSeq]
        match = False
        for i, tokensSeqGrouped in enumerate(grouped_words):
            tokensSeqGroupedI = [int(t) for t in tokensSeqGrouped]
            # If the current token sequence is contained within or overlaps with
            #  the token sequence group, then add it to the current group and
            #  exit.
            if (min(tokenSeqI) >= min(tokensSeqGroupedI) - 10 and max(tokenSeq) <= max(tokensSeqGroupedI) + 10) or \
               (min(tokenSeqI) - 10 <= min(tokensSeqGroupedI) <= max(tokenSeqI) + 10) or \
               (max(tokenSeqI) + 10 >= max(tokensSeqGroupedI) >= min(tokenSeqI) - 10):
               grouped_words[i] = tokensSeqGrouped + tokenSeq
               match = True
               break

        if not match:    # Sequence belongs to its own group (for now).
            grouped_words.append(tokenSeq)

    # Now build the snippet.
    combined_snippet = u""
    for tokenSeq in grouped_words:
        snippet = u""
        start_index = max(0, min([int(t) for t in tokenSeq])) - 5
        end_index = max([int(t) for t in tokenSeq]) + 5
        for i in range(start_index, end_index):
            match = re.search(r'<word id="'+str(i)+'">([^<]*)</word>', tokenizedContent, re.M|re.I)
            if not match:
                continue
            word = ""
            if str(i) in tokenSeq:
                # Tooltip shows the interpretation (Concept) for this
                #  Appellation.
                word = u"<strong data-toggle='tooltip' title='%s' class='text-warning text-snippet'>%s</strong>" % (annotation_map[str(i)], match.group(1))
            else:
                word = match.group(1)
            snippet = u'%s %s' % (snippet, word)
        combined_snippet += u' ...%s... ' % snippet.strip()
    return SafeText(combined_snippet)


def get_snippet(appellation):
    """
    Extract the text content surrounding (and including) an
    :class:`.Appellation` instance.

    Parameters
    ----------
    appellation : :class:`.Appellation`

    Returns
    -------
    snippet : :class:`django.utils.safestring.SafeText`
        Includes emphasis tags surrounding the :class:`.Appellation`\'s
        tokens.
    """
    if not appellation['tokenIds']:
        return SafeText('No snippet is available for this appellation')

    tokenizedContent = appellation['occursIn__tokenizedContent']
    annotated_words = appellation['tokenIds'].split(',')
    middle_index = int(annotated_words[max(len(annotated_words)/2, 0)])
    start_index = max(middle_index - 10, 0)
    end_index = middle_index + 10
    snippet = ""
    for i in range(start_index, end_index):
        match = re.search(r'<word id="'+str(i)+'">([^<]*)</word>', tokenizedContent, re.M|re.I)
        word = ""

        if str(i) in annotated_words:
            word = u"<strong class='text-warning text-snippet'>%s</strong>" % match.group(1)
        else:
            word = match.group(1)
        snippet = u'%s %s' % (snippet, word)
    return SafeText(u'...%s...' % snippet.strip())


@shared_task
def submit_relationsets_to_quadriga(relationsets, text, user):
    status, response = quadriga.submit_relationsets(relationsets, text, user)
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
