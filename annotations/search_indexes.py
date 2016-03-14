import datetime
from haystack import indexes
from annotations.models import Text

class TextIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    author = indexes.CharField(model_attr='addedBy')

    def get_model(self):
        return Text

    def index_queryset(self, using=None):
        return self.get_model().objects.all()