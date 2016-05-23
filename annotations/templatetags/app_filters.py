from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def safe_text(s):
    return mark_safe(s)

@register.filter
def current_fields(form):
    fields = []
    for field in form:
        print field.name, type(field), field.__dict__
        if field.value() and field.value()[0]:
            fields.append(field)
    return fields
