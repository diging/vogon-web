from django.db.models import Count

import datetime
from haystack import indexes
from annotations.models import Text
from concepts.models import Concept


class TextIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Index annotatable texts.
    """
    text = indexes.CharField(document=True, use_template=False)
    title = indexes.CharField(model_attr='title', indexed=False)
    created = indexes.DateField(model_attr='created', faceted=True, indexed=False, null=True)
    added = indexes.DateField(model_attr='added', faceted=True, indexed=False)
    addedBy = indexes.CharField(model_attr='addedBy')
    uri = indexes.CharField(model_attr='id')
    relation_count = indexes.CharField(model_attr='relation_count')

    def get_model(self):
        """ Get model to be used for indexing """
        return Text

    def index_queryset(self, using=None):
        """ Used when entire index for model is updated """
        return self.get_model().objects.all()

    def prepare_text(self, instance):
        return instance.title

    def prepare_added(self, instance):
        return instance.added.date()


class ConceptIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Index :class:`.Concept`\s that have been used in :class:`.Appellation`\s.
    """
    text = indexes.CharField(document=True, use_template=False)
    label = indexes.CharField(model_attr='label', indexed=False)
    typed = indexes.CharField(model_attr='typed', indexed=False, faceted=True)

    def get_model(self):
        return Concept

    def index_queryset(self, using=None):
        """
        Only index Concepts that have been used in annotations.
        """
        return self.get_model().objects.annotate(num_appellations=Count('appellation')).filter(num_appellations__gte=1)

    def prepare_text(self, instance):
        return self.prepare_label(instance)

    def prepare_label(self, instnace):
        return instance.label

    def prepare_typed(self, instance):
        if hasattr(instance, 'typed') and getattr(instance, 'typed'):
            return instance.typed.label
        return 'None'
