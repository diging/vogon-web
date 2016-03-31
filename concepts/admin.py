from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.template import RequestContext
from .models import *
from . import authorities
import django.forms as forms


def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
resolve.verbose_name = 'resolve selected concepts'

class SeriesForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

def merge_concepts(modeladmin, request, queryset):

        unResolvedConceptsList = queryset.exclude(concept_state = Concept.RESOLVED)
        resolvedConceptsList = queryset.filter(concept_state = Concept.RESOLVED)
        resolvedConcept = resolvedConceptsList[0]

        if request.method == 'POST':

            # process the queryset here
            unResolvedConceptsList.update(concept_state=Concept.REJECTED)
            unResolvedConceptsList.update(merged_with=resolvedConcept)

        else:
            opts = modeladmin.model._meta
            app_label = opts.app_label
            resolvedConceptCount = queryset.filter(concept_state = Concept.RESOLVED).count()

            #VGNWB-121 gets called only when there is only one resolved concept
            if resolvedConceptCount == 1:

            #As there will be only one element in the list
                form = SeriesForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

                context = {
                    "resolvedConcept": resolvedConcept,
                    "opts": opts,
                    "app_label": app_label,
                    "unResolvedConcepts": unResolvedConceptsList ,
                    "path" : request.get_full_path(),
                    "form" :form ,
                }

                return render_to_response('admin/merge_concepts_resolved.html', context, context_instance = RequestContext(request))

            return render_to_response('admin/merge_concepts.html', {'concepts': queryset})


class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = ('label',)
    list_display = ('label', 'description', 'resolved', 'concept_state', 'typed',)
    actions = (resolve,merge_concepts)
    list_filter=('concept_state', 'typed',)
    #opts = modeladmin.model._meta

class TypeAdmin(admin.ModelAdmin):
    model = Type
    list_display = ('label', 'resolved',)

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
