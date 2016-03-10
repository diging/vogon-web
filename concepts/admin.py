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

# def export_selected_objects(modeladmin, request, queryset):
#     selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
#     ct = ContentType.objects.get_for_model(queryset.model)
#     return HttpResponseRedirect("/export/?ct=%s&ids=%s" % (ct.pk, ",".join(selected)))
#
# class MergeAdmin(admin.ModelAdmin):
#     model = Merge
#     actions = ( export_selected_objects,    )
#     list_display = (    'label', 'resolved'  )

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
# admin.site.register(Merge, MergeAdmin)