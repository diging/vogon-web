import django_filters
from django_filters.fields import IsoDateTimeField
from django_filters import rest_framework as filters
from django.forms import DateTimeField
from annotations.models import RelationSet, TextCollection
from django.db.models import Q


class RelationSetFilter(django_filters.FilterSet):
    occursIn = django_filters.CharFilter('occursIn__uri', method='filter_occursIn')
    created = django_filters.DateTimeFromToRangeFilter()
    terminal_nodes = django_filters.CharFilter('terminal_nodes__uri')
    createdBy = django_filters.CharFilter('createdBy__username')


    def filter_occursIn(self, queryset, name, value): 
        if not value:
            return queryset
        return queryset.filter(Q(occursIn__uri=value) | Q(occursIn__part_of__uri=value) | Q(occursIn__part_of__part_of__uri=value))

    class Meta:
        model = RelationSet
        fields = ['createdBy', 'project', 'occursIn', 'terminal_nodes']


class ProjectFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    owner = filters.CharFilter(field_name='ownedBy__username', lookup_expr='icontains')
    collaborator = filters.NumberFilter(method='filter_collaborator', distinct=True)

    def filter_collaborator(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(ownedBy__pk=value) | Q(participants__pk=value)
        )

    class Meta:
        model = TextCollection
        fields = ['name', 'owner', 'collaborator']