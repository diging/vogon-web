"""
General-purpose helper functions.
"""

from django.conf import settings

from itertools import chain, combinations, groupby
import re

def help_text(text):
    """
    Remove excess whitespace from a string. Intended for use in model and form
    fields when writing long help_texts.
    """
    return re.sub('(\s+)', ' ', text)


def basepath(request):
    """
    Generate the base path (domain + path) for the site.

    TODO: Do we need this anymore?

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`

    Returns
    -------
    str
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return scheme + request.get_host() + settings.SUBPATH


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