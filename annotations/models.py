from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission
)
from django.utils.translation import ugettext_lazy as _

from concepts.models import Concept, Type
from annotations.managers import repositoryManagers

import ast


class VogonUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class VogonUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
    )

    affiliation = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    conceptpower_uri = models.URLField(max_length=500, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = VogonUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def __unicode__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class GroupManager(models.Manager):
    """
    The manager for the auth's Group model.
    """
    use_in_migrations = True

    def get_by_natural_key(self, name):
        return self.get(name=name)


class VogonGroup(models.Model):

    name = models.CharField(_('name'), max_length=80, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )

    objects = GroupManager()

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __init__(self):
        return self.name

    def natural_key(self):
        return (self.name,)



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

        try:
            value = ast.literal_eval(value)
        except ValueError:
            pass
        return value

    def get_prep_value(self, value):
        if value is None:
            return value

        return unicode(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


class TextCollection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    ownedBy = models.ForeignKey(VogonUser, related_name='collections')
    texts = models.ManyToManyField('Text', related_name='partOf',
                                   blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(VogonUser, related_name='contributes_to')


class Text(models.Model):
    uri = models.CharField(max_length=255, unique=True)
    """Should be sufficient to retrieve text from repository."""

    tokenizedContent = models.TextField()
    """Text should already be tagged, with <word> elements delimiting tokens."""

    title = models.CharField(max_length=255)
    created = models.DateField(blank=True, null=True)
    added = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey(VogonUser, related_name="addedTexts")
    source = models.ForeignKey("Repository", blank=True, null=True,
                               related_name="loadedTexts")
    originalResource = models.URLField(blank=True, null=True)
    annotators = models.ManyToManyField(VogonUser, related_name="userTexts")
    public = models.BooleanField(default=True)

    @property
    def annotationCount(self):
        return self.appellation_set.count() + self.relation_set.count()

    @property
    def relationCount(self):
        return self.relation_set.count()

    class Meta:
        permissions = (
            ('view_text', 'View text'),
        )


class Repository(models.Model):
    name = models.CharField(max_length=255)
    manager = models.CharField(max_length=255, choices=repositoryManagers)
    endpoint = models.CharField(max_length=255)

    oauth_client_id = models.CharField(max_length=255)
    oauth_secret_key = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.name)


class Authorization(models.Model):
    repository = models.ForeignKey('Repository')
    user = models.ForeignKey(VogonUser, related_name='authorizations')

    access_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=255)
    lifetime = models.IntegerField(default=0)
    refresh_token = models.CharField(max_length=255, blank=True)


class Annotation(models.Model):
    class Meta:
        abstract = True

    occursIn = models.ForeignKey("Text")
    created = models.DateTimeField(auto_now_add=True)
    createdBy = models.ForeignKey(VogonUser)


class Interpreted(models.Model):
    class Meta:
        abstract = True

    interpretation = models.ForeignKey(Concept)


class Appellation(Annotation, Interpreted):
    """
    An Appellation represents a user's interpretation of a specific passage of
    text. In particular, it captures the user's belief that the passage in
    question refers to a specific concept (e.g. of a person, place, etc).
    """

    tokenIds = models.TextField()
    """
    IDs of words (in the tokenizedContent) selected for this Appellation.
    """

    stringRep = models.TextField()
    """
    Plain-text snippet spanning the selected text.
    """

    startPos = models.IntegerField(blank=True, null=True)
    """
    Character offset from the beginning of the (plain text) document.
    """

    endPos = models.IntegerField(blank=True, null=True)
    """
    Character offset from the end of the (plain text) document.
    """

    # Reverse generic relations to Relation.
    relationsFrom = GenericRelation('Relation',
                                    content_type_field='source_content_type',
                                    object_id_field='source_object_id')
    relationsTo = GenericRelation('Relation',
                                    content_type_field='object_content_type',
                                    object_id_field='object_object_id')

    asPredicate = models.BooleanField(default=False)
    """
    Indicates whether this Appellation should function as a predicate for a
    Relation.
    """

    IS = 'is'
    HAS = 'has'
    NONE = None
    VCHOICES = (
        (NONE, ''),
        (IS, 'is/was'),
        (HAS, 'has/had'),
    )
    controlling_verb = models.CharField(max_length=4, choices=VCHOICES,
                                        null=True, blank=True, help_text="""
    Applies only if the Appellation is a predicate.""")


class Relation(Annotation):
    """
    A Relation captures a user's assertion that a passage of text implies a
    specific relation between two concepts.
    """

    # source = models.ForeignKey("Appellation", related_name="relationsFrom")
    source_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='as_source_in_relation')
    source_object_id = models.PositiveIntegerField()
    source_content_object = GenericForeignKey('source_content_type', 'source_object_id')

    predicate = models.ForeignKey("Appellation", related_name="relationsAs")

    # object = models.ForeignKey("Appellation", related_name="relationsTo")
    object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='as_object_in_relation')
    object_object_id = models.PositiveIntegerField()
    object_content_object = GenericForeignKey('object_content_type', 'object_object_id')

    # This should be replaced with more Relations.
    bounds = models.ForeignKey("TemporalBounds", blank=True, null=True)


class RelationTemplate(models.Model):
    """
    Provides a template for complex relations, allowing the user to simply
    fill in fields without worrying about the structure of the quadruple.

    TODO: add ``created_by`` field, perhaps others.
    """

    name = models.CharField(max_length=255)
    """A descriptive name used in menus in the annotation interface."""

    description = models.TextField()
    """A longer-form description of the relation."""


class RelationTemplatePart(models.Model):
    TYPE = 'TP'
    CONCEPT = 'CO'
    TOBE = 'IS'
    HAS = 'HA'
    RELATION = 'RE'
    NODE_CHOICES = (
        (TYPE, 'Concept type'),
        (CONCEPT, 'Specific concept'),
        (RELATION, 'Relation'),
    )
    PRED_CHOICES = (
        (TYPE, 'Concept type'),
        (CONCEPT, 'Specific concept'),
        (TOBE, 'Is/was'),
        (HAS, 'Has/had'),
    )

    part_of = models.ForeignKey('RelationTemplate', related_name="template_parts")

    internal_id = models.IntegerField(default=-1)

    source_node_type = models.CharField(choices=NODE_CHOICES, max_length=2)
    source_type = models.ForeignKey(Type, blank=True, null=True, related_name='used_as_type_for_source')
    source_concept = models.ForeignKey(Concept, blank=True, null=True, related_name='used_as_concept_for_source')
    source_relationtemplate = models.ForeignKey('RelationTemplatePart',  blank=True, null=True, related_name='used_as_source')
    source_relationtemplate_internal_id = models.IntegerField(default=-1)

    source_prompt_text = models.BooleanField(default=True)
    """Indicates whether the user should be asked for evidence for source."""
    source_description = models.TextField(blank=True, null=True)

    predicate_node_type = models.CharField(choices=PRED_CHOICES, max_length=2)
    predicate_type = models.ForeignKey(Type, blank=True, null=True, related_name='used_as_type_for_predicate')
    predicate_concept = models.ForeignKey(Concept, blank=True, null=True, related_name='used_as_concept_for_predicate')
    predicate_prompt_text = models.BooleanField(default=True)
    """Indicates whether the user should be asked for evidence for predicate."""
    predicate_description = models.TextField(blank=True, null=True)

    object_node_type = models.CharField(choices=NODE_CHOICES, max_length=2)
    object_type = models.ForeignKey(Type, blank=True, null=True, related_name='used_as_type_for_object')
    object_concept = models.ForeignKey(Concept, blank=True, null=True, related_name='used_as_concept_for_object')
    object_relationtemplate = models.ForeignKey('RelationTemplatePart',  blank=True, null=True, related_name='used_as_object')
    object_relationtemplate_internal_id = models.IntegerField(default=-1)
    object_prompt_text = models.BooleanField(default=True)
    """Indicates whether the user should be asked for evidence for object."""
    object_description = models.TextField(blank=True, null=True)


class TemporalBounds(models.Model):
    start = TupleField(blank=True, null=True)
    occur = TupleField(blank=True, null=True)
    end = TupleField(blank=True, null=True)
