from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from .models import *
from . import authorities
import django.forms as forms


from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html, html_safe
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)


def resolve(modeladmin, request, queryset):
    for obj in queryset:
        authorities.resolve(type(obj), obj)
resolve.verbose_name = 'resolve selected concepts'


class ConceptActionForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    action = forms.CharField(widget=forms.HiddenInput())
    confirmed = forms.BooleanField(initial=False, widget=forms.HiddenInput())


@html_safe
@python_2_unicode_compatible
class RadioChoiceInputWithDescription(forms.widgets.RadioSelect):
    def __init__(self, name, value, attrs, choice, index, **kwargs):
        self.name = name
        self.value = force_text(value)
        self.attrs = attrs
        self.choice_value = force_text(choice[0])
        self.choice_label = force_text(choice[1])
        self.index = index
        if 'id' in self.attrs:
            self.attrs['id'] += "_%d" % self.index

        self.description = kwargs.get('description', '')

    def render(self, name=None, value=None, attrs=None):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return mark_safe(force_text(format_html('<label{}>{} {} <p class="text-muted">{}</p></label>', label_for, self.tag(attrs), self.choice_label, self.description)))

    def __str__(self):
        return self.render()


@html_safe
@python_2_unicode_compatible
class RadioFieldRendererWithDescription(forms.widgets.Select):
    choice_input_class = RadioChoiceInputWithDescription

    def __str__(self):
        return self.render()

    def __init__(self, name, value, attrs, choices, **kwargs):
        self.name = name
        self.value = value
        self.attrs = attrs
        self.choices = choices
        self.descriptions = kwargs.get('descriptions', {})

    def __getitem__(self, idx):
        choice = self.choices[idx]  # Let the IndexError propagate
        description = self.descriptions.get(idx, '')
        return self.choice_input_class(self.name, self.value, self.attrs.copy(),
                                       choice, idx, description=description)

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id', None)
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = RadioFieldRendererWithDescription(
                                                      name=self.name,
                                                      value=self.value,
                                                      attrs=attrs_plus,
                                                      choices=choice_label)
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(format_html(self.inner_html, choice_value=choice_value,
                                          sub_widgets=sub_ul_renderer.render()))
            else:
                w = self.choice_input_class(self.name, self.value,
                                            self.attrs.copy(), choice, i,
                                            description=self.descriptions.get(choice_value, ''))
                output.append(format_html(self.inner_html,
                                          choice_value=force_text(w), sub_widgets=''))
        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class RadioSelectWithDescriptions(forms.widgets.RadioSelect):
    renderer = RadioFieldRendererWithDescription

    def __init__(self, *args, **kwargs):
        super(RadioSelectWithDescriptions, self).__init__(*args, **kwargs)

    def get_renderer(self, name, value, attrs=None, **kwargs):
        """Returns an instance of the renderer."""
        if value is None:
            value = self._empty_value
        final_attrs = self.build_attrs(attrs)
        descriptions = kwargs.get('descriptions', {})
        return self.renderer(name, value, final_attrs, self.choices,
                             descriptions=descriptions)

    def render(self, name, value, attrs=None):
        idx, label, description = list(zip(*self.choices))
        self.choices = list(zip(idx, label))
        self.descriptions = dict(list(zip(idx, description)))
        return self.get_renderer(name, value, attrs, descriptions=self.descriptions).render()


class ModelChoiceIteratorWithDescriptions(forms.models.ModelChoiceIterator):
    def choice(self, obj):
        return (self.field.prepare_value(obj),
                self.field.label_from_instance(obj),
                getattr(obj, 'description', ''))


class ModelChoiceFieldWithDescriptions(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super(ModelChoiceFieldWithDescriptions, self).__init__(*args, **kwargs)


    def _set_queryset(self, queryset):
        self._queryset = queryset
        idx, label, description = list(zip(*self._get_choices()))
        self.widget.choices = list(zip(idx, label))
        self.widget.descriptions = dict(list(zip(idx, description)))

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        if callable(value):
            value = CallableChoiceIterator(value)
        else:
            value = list(value)
        idx, label, description = list(zip(*value))
        self._choices = self.widget.choices = list(zip(idx, label))
        self.widget.descriptions = dict(list(zip(idx, description)))


    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, '_choices'):
            return self._choices
        return ModelChoiceIteratorWithDescriptions(self)

    choices = property(_get_choices, _set_choices)



class ConceptMergeForm(forms.Form):
    """
    The administrator can select one :class:`.Concept` instance into which all
    other selected :class:`.Concept` instances will be merged.
    """

    master_concept = ModelChoiceFieldWithDescriptions(required=False,
                                            queryset=Concept.objects.all(),
                                            widget=RadioSelectWithDescriptions(),
                                            empty_label=None)
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    action = forms.CharField(widget=forms.HiddenInput())


def traverse_mergers(concept):
    """
    Recursively collect all IDs for concepts that have been merged into
    ``concept``.
    """

    id_list = [concept.id]
    if concept.merged_concepts.count() > 0:
        for child in concept.merged_concepts.all():
            id_list += traverse_mergers(child)
    return id_list


def add_concepts_to_conceptpower(modeladmin, request, queryset):
    """
    Adds :class:`.Concept`\s in ``queryset`` to the Conceptpower authority
    service.

    TODO: add a confirmation step that shows similar concepts that already
    exist.

    Parameters
    ----------
    modeladmin
    request
    queryset
    """

    for concept in queryset:
        if concept.concept_state == Concept.APPROVED:
            response_data = authorities.add(concept)
            concept.uri = response_data['uri']
            concept.concept_state = Concept.RESOLVED
            concept.save()


def approve_concepts(modeladmin, request, queryset):
    for concept in queryset:
        concept.concept_state = Concept.APPROVED
        concept.save()


def perform_merge(unresolved_concepts, master_concept):
    """
    Merge a set of unresolved concepts into a single master concept.
    """

    unresolved_concepts.update(concept_state=Concept.REJECTED)

    # merged_with indicates that a rejected concept has been merged with
    #  another concept.
    unresolved_concepts.update(merged_with=master_concept)

    # It may be the case that other concepts have been merged into these
    #  unresolved concepts. Therefore, we recursively collect all of
    #  these "child" concepts, and point them to the master concept.
    children = []
    for concept in unresolved_concepts:
        children += traverse_mergers(concept)
    children_queryset = Concept.objects.filter(pk__in=children)
    children_queryset.update(merged_with=master_concept)


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
        POST request.
    """

    # There must be at least two concepts to perform a merge action (merging a
    #  concept into itself doesn't make any sense).
    if queryset.count() < 2:
        # This will display a green message above the list of concepts.
        modeladmin.message_user(request, 'Please select at least two concepts')
        return

    # Approved concepts should be treated just like resolved concepts; the
    #  only difference is that they have not yet been added to the remote
    #  authority service.
    resolved_condition = Q(concept_state=Concept.RESOLVED) | \
                         Q(concept_state=Concept.APPROVED)
    resolved_concepts = queryset.filter(resolved_condition)

    # Once a concept is resolved, it is immutable: it cannot be changed, merged,
    #  deleted, etc.
    if resolved_concepts.count() > 1:
        # Again, green message to the user at the top of the page.
        modeladmin.message_user(request, "You cannot select more than one"
                                         " resolved concept.")
        return

    # Allows us to pass around the Concept queryset between steps.
    _selected_action_ids = [obj['id'] for obj in queryset.values('id')]

    # When there is only one resolved concept, we direct the user to an
    #  intermediate form for confirmation to resolve unresolvedConcepts into
    #  resolved Concept.
    if resolved_concepts.count() == 1:
        merged_condition = Q(merged_with__isnull=False)

        # It is OK to merge a Rejected concept, but only if it is not already
        #  merged into another concept.
        unresolved_condition = Q(concept_state=Concept.PENDING) | \
                               Q(Q(merged_with__isnull=True) & \
                                 Q(concept_state=Concept.REJECTED))
        unresolved_concepts = queryset.filter(unresolved_condition)

        action_form = ConceptActionForm(request.POST)

        # If the user confirms the merge action, then we should proceed with
        #  merging the unresolved concepts into the resolved (master) concept.
        if action_form.is_valid() and action_form.cleaned_data['confirmed']:
            try:
                perform_merge(unresolved_concepts, resolved_concepts.first())
            except Exception as E:
                error_message = 'Encountered unhandled exception: %s' % str(E)
                modeladmin.message_user(request, error_message)

            modeladmin.message_user(request, "Concepts merged successfully")
            return

        else:
            action_form = ConceptActionForm({
                '_selected_action': _selected_action_ids,
                'action': 'merge_concepts',
                'confirmed': True,
            })

            context = {
                "resolvedConcept": resolved_concepts.first(),
                "opts": modeladmin.model._meta,
                "app_label": modeladmin.model._meta.app_label,
                "unresolved_concepts": unresolved_concepts ,
                "path" : request.get_full_path(),
                "action_form": action_form,
            }

            return render(request, 'admin/merge_concepts_resolved.html', context)

    # When there is no resolved concept, we display a form asking the user to
    #  select which concept should be the master concept (into which the other
    #  concepts will be merged).
    elif resolved_concepts.count() == 0:
        merge_form = ConceptMergeForm(request.POST)

        # If the user has selected a master concept, then we need to execute the
        #  merge action.
        if merge_form.is_valid() and merge_form.cleaned_data['master_concept']:
            master_concept = merge_form.cleaned_data['master_concept']
            unresolved_concepts = queryset.exclude(pk=master_concept.id)
            try:
                perform_merge(unresolved_concepts, master_concept)
            except Exception as E:
                error_message = 'Encountered unhandled exception: %s' % str(E)
                modeladmin.message_user(request, error_message)

            modeladmin.message_user(request, "Concepts merged successfully")
            return

        # We must prompt the user to select a master concept.
        else:
            merge_form = ConceptMergeForm({
                '_selected_action': _selected_action_ids,
                'action': 'merge_concepts',
            })
            merge_form.fields['master_concept'].queryset = queryset
            context = {
                'form': merge_form,
            }
            # merge_form.fields['master_concept'].
            return render(request, 'admin/merge_concepts.html', context)


class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    search_fields = ('label',)
    list_display = ('label', 'description', 'concept_state', 'typed',)
    actions = (merge_concepts, approve_concepts, add_concepts_to_conceptpower,
               resolve)
    list_filter = ('concept_state', 'typed',)

    # def get_queryset(self, request):
    #     """
    #     Only show Rejected concepts if explicitly requested via the changelist
    #     filter.
    #     """
    #     qs = super(ConceptAdmin, self).get_queryset(request)
    #     if request.GET.get('concept_state__exact', None) == 'Rejected':
    #         return qs
    #     return qs.filter(~Q(concept_state=Concept.REJECTED))


class TypeAdmin(admin.ModelAdmin):
    model = Type
    list_display = ('label', 'resolved',)

admin.site.register(Concept, ConceptAdmin)
admin.site.register(Type, TypeAdmin)
