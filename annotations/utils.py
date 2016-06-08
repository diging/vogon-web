"""
General-purpose helper functions.
"""

import re


def help_text(text):
    """
    Remove excess whitespace from a string. Intended for use in model and form
    fields when writing long help_texts.
    """
    return re.sub('(\s+)', ' ', text)
