from django.db import models
from concepts.models import Concept
import ast

from annotations.managers import repositoryManagers

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission
)
from django.utils.translation import ugettext_lazy as _


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
    tokenIds = models.TextField()
    stringRep = models.TextField()
    startPos = models.IntegerField(blank=True, null=True)
    endPos = models.IntegerField(blank=True, null=True)

    asPredicate = models.BooleanField(default=False)

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
    source = models.ForeignKey("Appellation", related_name="relationsFrom")
    predicate = models.ForeignKey("Appellation", related_name="relationsAs")
    object = models.ForeignKey("Appellation", related_name="relationsTo")

    bounds = models.ForeignKey("TemporalBounds", blank=True, null=True)


class TemporalBounds(models.Model):
    start = TupleField(blank=True, null=True)
    occur = TupleField(blank=True, null=True)
    end = TupleField(blank=True, null=True)
