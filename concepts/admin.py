from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.template import RequestContext
from .models import *
from . import authorities


def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
resolve.verbose_name = 'resolve selected concepts'

def merge_concepts(modeladmin, request, queryset):
    """
    This method gets called when we click on "Merge Concepts" action after we select the concepts
    from the list of concepts
    :param modeladmin:
    :param request:
    :param queryset:
    :return:
    """
    #return render_to_response('admin/Sample.html')
    RESOLVED_STATUS = Concept.RESOLVED


    if 'post' in request.POST:
            # process the queryset here

        unResolvedConceptsList = queryset.exclude(concept_state = RESOLVED_STATUS).values()
        resolvedConceptsList = queryset.filter(concept_state = RESOLVED_STATUS).values()
        resolvedConcept = resolvedConceptsList[0]

        for i in range(0,len(unResolvedConceptsList)):
            presentConcept = unResolvedConceptsList.get(i)
            presentConcept.merged_with = resolvedConcept
            presentConcept.concept_state = Concept.REJECTED

        return render_to_response('admin/Sample.html')
    else:
        opts = modeladmin.model._meta
        app_label = opts.app_label

        resolvedConceptCount = queryset.filter(concept_state = RESOLVED_STATUS).count()

    #VGNWB-121 gets called only when there is only one resolved concept
        if resolvedConceptCount == 1:
            resolvedConceptsList = queryset.filter(concept_state = RESOLVED_STATUS).values()
            unResolvedConceptsList = queryset.exclude(concept_state = RESOLVED_STATUS).values()

            #As there will be only one element in the list
            resolvedConcept = resolvedConceptsList[0]
            resolvedConceptName = resolvedConcept['label']

            context = {
                "resolvedConcept": resolvedConceptName,
                "opts": opts,
                "app_label": app_label,
                "unResolvedConcepts": unResolvedConceptsList ,
                "path" : request.get_full_path(),

            }
            return render_to_response('admin/merge_concepts_resolved.html', context, context_instance = RequestContext(request),)

        return render_to_response('admin/merge_concepts.html', {'concepts': queryset})


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
