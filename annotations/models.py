from django.db import models
from django.contrib.auth.models import User
from concepts.models import Concept
import ast


class TupleField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a Python tuple of instances of built-in types"

    def __init__(self, *args, **kwargs):
        super(TupleField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = tuple()

        if isinstance(value, tuple):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return unicode(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


class TextCollection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    ownedBy = models.ForeignKey(User, related_name='collections')
    texts = models.ManyToManyField('Text', related_name='partOf', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

class Text(models.Model):
    uri = models.CharField(max_length=255, unique=True)
    """Should be sufficient to retrieve text from repository."""

    tokenizedContent = models.TextField()
    """Text should already be tagged, with <word> elements delimiting tokens."""

    title = models.CharField(max_length=255)
    created = models.DateField(blank=True, null=True)

    added = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey(User, related_name="addedTexts")

    source = models.ForeignKey("Repository", related_name="loadedTexts")

    originalResource = models.URLField(blank=True, null=True)

    annotators = models.ManyToManyField(User, related_name="userTexts")

    @property
    def annotationCount(self):
        return self.appellation_set.count() + self.relation_set.count()


class Repository(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.name)


class Annotation(models.Model):
    class Meta:
        abstract = True

    occursIn = models.ForeignKey("Text")
    created = models.DateTimeField(auto_now_add=True)
    createdBy = models.ForeignKey(User)


class Interpreted(models.Model):
    class Meta:
        abstract = True

    interpretation = models.ForeignKey(Concept)


class Appellation(Annotation, Interpreted):
    tokenIds = models.TextField()
    stringRep = models.TextField()
    startPos = models.IntegerField(blank=True, null=True)
    endPos = models.IntegerField(blank=True, null=True)

    asPredicate = models.BooleanField(default=False)


class Relation(Annotation):
    source = models.ForeignKey("Appellation", related_name="relationsFrom")
    predicate = models.ForeignKey("Appellation", related_name="relationsAs")
    object = models.ForeignKey("Appellation", related_name="relationsTo")

    bounds = models.ForeignKey("TemporalBounds", blank=True, null=True)


class TemporalBounds(models.Model):
    start = TupleField(blank=True, null=True)
    occur = TupleField(blank=True, null=True)
    end = TupleField(blank=True, null=True)
