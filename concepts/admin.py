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
    """
    An administrator should be able to merge concepts in the concept change list
    view.

    Parameters
    ----------
    modeladmin : :class:`.ConceptAdmin`
    request : :class:`HttpRequest`
    queryset : :class:`QuerySet`
        Should contain two or more :class:.`Concept` instances.


    Returns
    -------
    HttpResponse
    """

    # There must be at least two concepts to perform a merge action (merging a
    #  concept into itself doesn't make any sense).
    if queryset.count() < 2:
        modeladmin.message_user(request, 'Please select at least two concepts')
        return

    unResolvedConceptsList = queryset.exclude(concept_state = Concept.RESOLVED)
    resolvedConceptsList = queryset.filter(concept_state = Concept.RESOLVED)

    if resolvedConceptsList.count() > 0:
        resolvedConcept = resolvedConceptsList[0]

    #When the user confirms in the intermediate page obtained when there is only one
    #resolved concept, then we enter below block
    if 'submitmergeaction' in request.POST:

        unResolvedConceptsList.update(concept_state=Concept.REJECTED)
        unResolvedConceptsList.update(merged_with=resolvedConcept)

    else:
        opts = modeladmin.model._meta
        app_label = opts.app_label
        resolvedConceptCount = queryset.filter(concept_state = Concept.RESOLVED).count()

        #when there is only one resolved concept, we direct to intermediate form
        #for confirmation to resolve unresolvedConcepts into resolved Concept
        if resolvedConceptCount == 1:

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

        #when there is more than one resolved concept, we display the summary of concepts
        #to be merged in intermediate form
        return render_to_response('admin/merge_concepts.html', {'concepts': queryset})

class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = ('label',)
    list_display = ('label', 'description', 'resolved', 'concept_state', 'typed',)
    actions = (resolve, merge_concepts)
    list_filter=('concept_state', 'typed',)
    #opts = modeladmin.model._meta

class TypeAdmin(admin.ModelAdmin):
    model = Type
    list_display = ('label', 'resolved',)

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
