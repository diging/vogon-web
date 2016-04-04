import datetime
from haystack import indexes
from annotations.models import Text

class TextIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    addedBy = indexes.CharField(model_attr='addedBy')
    uri = indexes.CharField(model_attr='id')
    relation_count = indexes.CharField(model_attr='relation_count')

    def get_model(self):
        return Text

    def index_queryset(self, using=None):
        x = self.get_model()
        y = x.objects
        z = y.get_queryset().order_by('title')
        return z

    def read_queryset(self, using=None):
        x = self.index_queryset(using=using).order_by('title')
        return x

    def load_all_queryset(self):
        x = self.get_model()
        y = x.objects
        z = y.get_queryset().order_by('title')
        return z
