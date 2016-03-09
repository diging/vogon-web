from django.contrib import admin
from .models import *

from . import authorities

def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
resolve.verbose_name = 'resolve selected concepts'

class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = ('label',)
    list_display = ('label', 'resolved', 'concept_state', 'typed',)
    actions = (resolve,)
    list_filter=('concept_state', 'typed',)

class TypeAdmin(admin.ModelAdmin):
    model = Type

    list_display = ('label', 'resolved',)

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
