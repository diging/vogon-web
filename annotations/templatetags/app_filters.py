from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def safe_text(s):
    return mark_safe(s)
