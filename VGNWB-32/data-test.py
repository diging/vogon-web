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
from django.contrib.auth.models import User
from concepts.models import Concept

#print_obj = Appellation.objects.all()
print_obj = Relation.objects.all()

print "--------------------------------------------------"
print "                    Object                        "
print "--------------------------------------------------"
for obj in print_obj:
	print "Type : ", type(obj), type(obj.__dict__)
	print "Object : ", obj.__dict__
#	xml = dicttoxml.dicttoxml(rel.__dict__)
	obj = obj.__dict__
	for k, v in obj.iteritems():
		print k, "	: ", v
		#print type(elem)
	print "---"


#------------- XML BUILD LOGIC -------------------

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i



import xml.etree.ElementTree as ET

rel = Relation.objects.all()[0]

def create_relation(rel):
	root = ET.Element("relation_event")
	id = ET.SubElement(root, "id")
	creator = ET.SubElement(root, "creator")
	creator.text = rel.createdBy.username

	creation_date = ET.SubElement(root, "creation_date")
	creation_date.text = str(rel.created)

	creation_place = ET.SubElement(root, "creation_place")

	source_reference = ET.SubElement(root, "source_reference")

	interpretation_creator = ET.SubElement(root, "interpretation_creator")

	relation = ET.SubElement(root, "relation")

	rel_id = ET.SubElement(relation, "id")

	creator = ET.SubElement(relation, "creator")
	creator.text = rel.createdBy.username

	creation_date = ET.SubElement(relation, "creation_date")
	subject = ET.SubElement(relation, "subject")
	subject_obj = Appellation.objects.filter(id = rel.source_id)
	subject.text = subject_obj[0].stringRep

	object = ET.SubElement(relation, "object")
	object_obj = Appellation.objects.filter(id = rel.object_id)
	object.text = object_obj[0].stringRep

	predicate = ET.SubElement(relation, "predicate")
	predicate_obj = Appellation.objects.filter(id = rel.predicate_id)
	predicate.text = predicate_obj[0].stringRep

	indent(root)
	quadruple = ET.dump(root)
	return quadruple

print create_relation(rel)
