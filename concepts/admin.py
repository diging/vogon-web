from django.contrib import admin
from .models import *
from .models import Concept
from django.shortcuts import render_to_response

from . import authorities
from django.http import HttpResponse
from django.core import serializers


def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
#resolve.verbose_name = 'resolve selected concepts'

def merge_concepts(modeladmin, request, queryset):

    opts = modeladmin.model._meta
    app_label = opts.app_label

    RESOLVED_STATUS = 'Resolved'
    #presentVal = ''
    resolvedCount = 0
    resolvedConcept = None

    for item in queryset:
        if item.concept_state == RESOLVED_STATUS:
            resolvedCount += 1
            resolvedConcept = item

    context = {
        "resolvedConcept":resolvedConcept,
        "opts": opts,
        "app_label": app_label
    }

    if resolvedCount == 1:
        #return render_to_response('admin/merge_concepts.html', {'resolvedConcept':resolvedConcept
                                                        #,'app_label':app_label, 'opts':opts })
        return render_to_response('admin/merge_concepts.html', context)

    return render_to_response('admin/merge_concepts_2.html', {'concepts': queryset})
    #for item in queryset:
    #    print item

class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = (   'label',    )
    list_display = (    'label', 'resolved','concept_state'  )
    actions = ( resolve, merge_concepts   )

    list_filter=('concept_state',)

class TypeAdmin(admin.ModelAdmin):
    model = Type

    list_display = (    'label', 'resolved'  )

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)


