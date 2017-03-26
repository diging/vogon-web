import django_filters
from django_filters.fields import IsoDateTimeField
from django.forms import DateTimeField
from concepts.models import Concept, Type
from django.db.models import Q


class ConceptFilter(django_filters.FilterSet):

    class Meta:
        model = Concept
        fields = ['authority', 'pos', 'concept_state', 'typed',]
