from django.db import models
from annotations.models import VogonUser
# Create your models here.

class GithubToken(models.Model):
	token = models.CharField(max_length=50)
	user = models.ForeignKey(VogonUser, on_delete=models.CASCADE)