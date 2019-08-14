from django.db import models, IntegrityError
from annotations.models import VogonUser as User


class GilesToken(models.Model):
    """
    A short-lived auth token for sending content to Giles on behalf of a user.

    See https://diging.atlassian.net/wiki/display/GIL/REST+Authentication.
    """

    for_user = models.OneToOneField(User, related_name='giles_token', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=255)
