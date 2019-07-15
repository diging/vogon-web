from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

optional = { 'blank': True, 'null': True }


class HeritableObject(models.Model):
    """
    An object that is aware of its "real" type, i.e. the subclass that it
    instantiates.
    """

    real_type = models.ForeignKey(ContentType, editable=False, on_delete=models.CASCADE)
    label = models.CharField(max_length=255, **optional)

    def save(self, *args, **kwargs):
        if not self.id or not self.real_type:
            self.real_type = self._get_real_type()
        super(HeritableObject, self).save(*args, **kwargs)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        """
        Re-cast this object using its "real" subclass.
        """

        return self.real_type.get_object_for_this_type(pk=self.pk)

    def __unicode__(self):
        return str(self.label)

    class Meta:
        abstract = True


class Concept(HeritableObject):
    uri = models.CharField(max_length=255, unique=True)
    resolved = models.BooleanField(default=False)
    typed = models.ForeignKey('Type', related_name='instances', **optional, on_delete=models.CASCADE)
    description = models.TextField(**optional)
    authority = models.CharField(max_length=255, blank=True, null=True)
    pos = models.CharField(max_length=255, **optional)

    PENDING = 'Pending'
    REJECTED = 'Rejected'
    APPROVED = 'Approved'
    RESOLVED = 'Resolved'
    MERGED = 'Merged'
    concept_state_choices=  (
        (PENDING, 'Pending'),
        (REJECTED, 'Rejected'),
        (APPROVED, 'Approved'),
        (RESOLVED, 'Resolved'),
        (MERGED, 'Merged'),
    )
    concept_state=models.CharField(max_length=10, choices=concept_state_choices,
                                   default='Pending')
    merged_with = models.ForeignKey('Concept', related_name='merged_concepts',
                                    **optional, on_delete=models.CASCADE)

    @property
    def typed_label(self):
        if self.typed:
            return self.typed.label
        return None

    def __unicode__(self):
        if self.label:
            return self.label
        return self.uri

    @property
    def children(self):
        def traverse_mergers(concept):
            """
            Recursively collect all IDs for concepts that have been merged into
            ``concept``.
            """

            id_list = [concept.id]
            if concept.merged_concepts.count() > 0:
                for child in concept.merged_concepts.all():
                    id_list += traverse_mergers(child)
            return id_list
        return traverse_mergers(self)

    def get_absolute_url(self):
        return reverse('concept', args=(self.id,))

    @property
    def master(self):
        """
        Get the highest-level merge target.
        """
        _visited = set()
        def _get(concept):
            if concept.id in _visited:
                raise RuntimeError("Circular merge chain::: %s" % ', '.join(map(str, list(visited))))
            _visited.add(concept.id)
            if concept.merged_with:
                return _get(concept.merged_with)
            return concept
        return _get(self)


class Type(Concept):
    pass
