import datetime
from haystack import indexes
from annotations.models import Text

class TextIndex(indexes.SearchIndex, indexes.Indexable):
    """ Create search index to tell haystack what data to be placed in search index"""
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
