from django.db import models
from django.contrib.auth.models import User
from concepts.models import Concept
import ast
import dicttoxml

#---------- LOCAL SETTINGS COMMAND -------------------
import os
os.system("export REDIS_URL=redis://")
os.system("export DJANGO_SETTINGS_MODULE='vogon.local_settings'")



from annotations.managers import repositoryManagers

from annotations.models import *

text_obj = Text.objects.all()
relation_obj = Relation.objects.all()
appellation_obj = Appellation.objects.all()

print "--------------------------------------------------"
print "                     TEXT                         "
print "--------------------------------------------------"
for txt in text_obj:
	print "Type : ", type(txt), type(txt.__dict__)
	print "Object : ", txt.__dict__
#	xml = dicttoxml.dicttoxml(rel.__dict__)
	obj = txt.__dict__
	for k, v in obj.iteritems():
		print k, "	: ", v
		#print type(elem)
	print "---"



print "--------------------------------------------------"
print "                   RELATIONS                      "
print "--------------------------------------------------"
for rel in relation_obj:
	print "Type : ", type(rel), type(rel.__dict__)
	print "Object : ", rel.__dict__
#	xml = dicttoxml.dicttoxml(rel.__dict__)
	obj = rel.__dict__
	for k, v in obj.iteritems():
		print k, "	: ", v
		#print type(elem)
	print "---"

print "--------------------------------------------------"
print "                  APPELLATION                     "
print "--------------------------------------------------"

for appe in appellation_obj:
	obj = rel.__dict__
	print "Object : ", obj
	for k, v in obj.iteritems():
		print k, "	: ", v
	#print appe.__dict__
	print "---------------------------------------"
