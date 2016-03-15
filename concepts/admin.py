from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from .models import *

from . import authorities

def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
resolve.verbose_name = 'resolve selected concepts'

def merge_concepts(self, request, queryset):
    return render_to_response('admin/merge_concepts.html', {'concepts': queryset})
merge_concepts.verbose_name = "Merge Concepts"

class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = ('label',)
    list_display = ('label', 'resolved', 'concept_state', 'typed',)
    actions = (resolve, merge_concepts,)
    list_filter=('concept_state', 'typed',)

class TypeAdmin(admin.ModelAdmin):
    model = Type
    list_display = ('label', 'resolved',)

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
