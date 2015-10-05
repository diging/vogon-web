import requests
from bs4 import BeautifulSoup

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

def extract_text_file(text_file):
    for line in text_file:
        print line

def extract_pdf_file(pdf_file):
    # TODO: Use slate library
    for line in pdf_file:
        print line
