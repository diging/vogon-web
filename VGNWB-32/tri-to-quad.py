
from django.db import models
from django.contrib.auth.models import User
from concepts.models import Concept
import ast

from annotations.managers import repositoryManagers

from annotations.models import *



relation_obj = Relation.objects.all()
appellation_obj = appellations.objects.all()

for rel in relation_obj:
	print rel.__dict__

for appe in appellation_obj:
	print appe.__dict__


