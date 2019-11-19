from django.db import models
from annotations.models import VogonUser

import datetime, json

from goat.authorities import AuthorityManager


opt = {'blank': True, 'null': True}


class BasicAccessionMixin(models.Model):
    """
    Basic data tracking information.
    """
    class Meta:
        abstract = True

    added_by = models.ForeignKey(VogonUser, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Authority(BasicAccessionMixin):
    """
    An Authority service, system, file, or other source of concepts.
    """
    name = models.CharField(max_length=255)
    namespace = models.CharField(max_length=255, **opt)
    description = models.TextField(**opt)

    configuration = models.TextField(**opt)
    """JSON-serialized configuration (if available) for this authority."""

    builtin_identity_system = models.ForeignKey('IdentitySystem', on_delete=models.CASCADE, **opt)

    @property
    def manager(self):
        if not self.configuration:
            raise AttributeError("Configuration unavailable for %s" % self.name)
        return AuthorityManager(self.configuration)

    @property
    def get(self):
        return self.manager.get

    @property
    def search(self):
        return self.manager.search

    def accepts(self, method, *params):
        return self.manager.accepts(method, *params)

    def __str__(self):
        return self.name


class Concept(BasicAccessionMixin):
    """
    Represents a single entry in an authority service or system.

    For example, this might be an entry for a particular person in the Library
    of Congress or VIAF.
    """

    authority = models.ForeignKey('Authority', related_name='concepts', on_delete=models.CASCADE, **opt)
    """The authority system to which this concept belongs."""

    name = models.CharField(max_length=255)
    """Primary name or label, used for search and display."""

    identifier = models.CharField(max_length=255, unique=True)
    """
    The URI for this concept.
    """

    local_identifier = models.CharField(max_length=255, **opt)
    """
    The symbol used by ``authority`` internally to identify this concept.
    """

    description = models.TextField(null=True, blank=True)
    """If available, a freeform description provided by the authority."""

    data = models.TextField(blank=True, null=True)
    """JSON-pickled data about this concept from the authority service."""

    concept_type = models.ForeignKey('Concept', related_name='instances', on_delete=models.CASCADE, **opt)
    """
    Some authority systems may have type ontologies. Types should be treated as
    concepts.
    """

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.authority:
            for authority in Authority.objects.all():
                if not authority.namespace:
                    continue
                if authority.namespace in self.identifier:
                    self.authority = authority
                    break
        super(Concept, self).save(*args, **kwargs)


class IdentitySystem(BasicAccessionMixin):
    """
    An identity system organizes a set of identity propositions about concepts.

    This allows many different identity models to coexist for different
    purposes, without having to commit to a particular view of the world.
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Identity(BasicAccessionMixin):
    """
    An identity proposition about a set of concepts.
    """

    name = models.CharField(max_length=255, **opt)
    """Can be used to provide an appellation for the cluster of concepts."""

    part_of = models.ForeignKey('IdentitySystem', on_delete=models.CASCADE, related_name='identities')
    """The system to which this identity belongs."""

    confidence = models.FloatField(default=1.0, blank=True, null=True)
    """This can (optionally) be used to express relative confidence levels."""

    concepts = models.ManyToManyField('Concept', related_name='identities')
    """The concepts asserted to be identical."""

    def __str__(self):
        return self.name
