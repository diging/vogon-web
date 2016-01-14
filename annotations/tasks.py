"""
We should probably write some documentation.
"""


from django.contrib.auth.models import Group
import requests
from bs4 import BeautifulSoup
from models import Text
from guardian.shortcuts import assign_perm
import uuid

import slate
from . import managers

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
