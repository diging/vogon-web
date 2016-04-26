from django.db import models
from django.contrib.contenttypes.models import ContentType

optional = { 'blank': True, 'null': True }


class HeritableObject(models.Model):
    """
    An object that is aware of its "real" type, i.e. the subclass that it
    instantiates.
    """

    real_type = models.ForeignKey(ContentType, editable=False)
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
        return unicode(self.label)

    class Meta:
        abstract = True


class Concept(HeritableObject):
    uri = models.CharField(max_length=255, unique=True)
    resolved = models.BooleanField(default=False)
    typed = models.ForeignKey('Type', related_name='instances', **optional )
    description = models.TextField(**optional)
    authority = models.CharField(max_length=255)
    pos = models.CharField(max_length=255, **optional)
    PENDING = 'Pending'
    REJECTED = 'Rejected'
    APPROVED = 'Approved'
    RESOLVED = 'Resolved'
    concept_state_choices=  (
        (PENDING, 'Pending'),
        (REJECTED, 'Rejected'),
        (APPROVED, 'Approved'),
        (RESOLVED, 'Resolved'),
    )
    concept_state=models.CharField(max_length=10, choices=concept_state_choices,
                                   default='Pending')
    merged_with = models.ForeignKey('Concept', related_name='merged_concepts',
                                    **optional)

    @property
    def typed_label(self):
        if self.typed:
            return self.typed.label
        return None


class Type(Concept):
    pass
