from django.db import models
from django.contrib.auth.models import User
from concepts.models import Concept

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


class Repository(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.name)


class Session(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    """A session can be (optionally) given a name."""

    created = models.DateTimeField(auto_now_add=True)
    createdBy = models.ForeignKey(User)
    updated = models.DateTimeField(auto_now=True)


class Annotation(models.Model):
    class Meta:
        abstract = True

    occursIn = models.ForeignKey("Text")
    created = models.DateTimeField(auto_now_add=True)
    createdBy = models.ForeignKey(User)
    inSession = models.ForeignKey("Session")


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


class TemporalBounds(Appellation):
    start = models.DateField(blank=True, null=True)
    occur = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

