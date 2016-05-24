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
        value = field.value()
        if value and value[0]:
            if hasattr(field.field, 'choices'):
                choices = dict(field.field.choices)
                if type(value) is list:
                    value = '; '.join([choices[int(v)] for v in value])
                else:
                    value = choices[int(value)]

            fields.append((field.name.title(), value))
    return fields
