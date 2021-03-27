from django.db import models
from annotations.models import VogonUser
# Create your models here.

class GithubToken(models.Model):
	token = models.CharField(max_length=50)
	user = models.ForeignKey(VogonUser, on_delete=models.CASCADE)

class CitesphereToken(models.Model):
	token = models.CharField(max_length=50)
	user = models.ForeignKey(VogonUser, on_delete=models.CASCADE)

class ResetToken(models.Model):
	token = models.CharField(max_length=1000)
	user = models.ForeignKey(VogonUser, on_delete=models.CASCADE)

	def __str__(self):
		return f"Token <{self.user.username}>"
