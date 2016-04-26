import datetime
from haystack import indexes
from annotations.models import Text

class TextIndex(indexes.SearchIndex, indexes.Indexable):
    """ Create search index to tell haystack what data to be placed in search index"""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', indexed=False)
    addedBy = indexes.CharField(model_attr='addedBy')
    uri = indexes.CharField(model_attr='id')
    relation_count = indexes.CharField(model_attr='relation_count')

    def get_model(self):
        """ Get model to be used for indexing """
        return Text

    def index_queryset(self, using=None):
        """ Used when entire index for model is updated """
        return self.get_model().objects.all()
