import django_filters
from django_filters.fields import IsoDateTimeField
from django.forms import DateTimeField
from annotations.models import RelationSet
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
