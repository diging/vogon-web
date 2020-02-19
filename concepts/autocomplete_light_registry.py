import autocomplete_light
import autocomplete_light.shortcuts as al
from .models import Concept


class ConceptAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    search_fields=['^label',]

    autocomplete_js_attributes = {
        'minimum_characters': 2,
    }

    widget_js_attributes = {
        'max_values': 1,
        'choice_selector': '[data-url]?pos=noun'

    }

    def choices_for_request(self):
        """
        Return choices for a particular request.
        """
        assert self.choices is not None, 'choices should be a queryset'
        assert self.search_fields, 'autocomplete.search_fields must be set'
        q = self.request.GET.get('q', '')
        exclude = self.request.GET.getlist('exclude')

        conditions = self._choices_for_request_conditions(q, self.search_fields)

        pos = self.request.GET.get('pos', None)
        queryset = self.choices.filter(conditions).exclude(pk__in=exclude)
        if pos:
            queryset = queryset.filter(pos=pos)

        return self.order_choices(queryset)[0:self.limit_choices]

al.register(Concept, ConceptAutocomplete)
