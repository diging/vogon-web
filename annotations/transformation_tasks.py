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

print_obj = Appellation.objects.all()
#print_obj = Relation.objects.all()

'''
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

'''

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

def create_relation(rel):
	#import xml.etree.ElementTree as ET
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
	subject_obj = Appellation.objects.filter(id = rel.source_id)[0]
	subject.append(create_appellation(subject_obj))

	#subject.text = subject_obj[0].stringRep

	object = ET.SubElement(relation, "object")
	object_obj = Appellation.objects.filter(id = rel.object_id)[0]
	object.append(create_appellation(object_obj))
	#object.text = object_obj[0].stringRep

	predicate = ET.SubElement(relation, "predicate")
	predicate_obj = Appellation.objects.filter(id = rel.predicate_id)[0]
	predicate.append(create_appellation(predicate_obj))
	#predicate.text = predicate_obj[0].stringRep

	#indent(root)
	#quadruple = ET.dump(root)
	#return quadruple
	return root


def create_appellation(appln, parent = None):
	#appln = Appellation.objects.filter(id = appln_id)
	if parent == None :
		root = ET.Element("appellation_event")
	else:
		root = ET.Element(parent, "appellation_event")
	id = ET.SubElement(root, "id")
	creator = ET.SubElement(root, "creator")
	creator.text = appln.createdBy.username

	creation_date = ET.SubElement(root, "creation_date")
	creation_date.text = str(appln.created)

	creation_place = ET.SubElement(root, "creation_place")

	source_reference = ET.SubElement(root, "source_reference")

	term = ET.SubElement(root, "term")
	#-----------------
	t_id = ET.SubElement(term, "id")
	t_creator = ET.SubElement(term, "creator")
	t_creator.text = appln.createdBy.username

	t_creation_date = ET.SubElement(term, "creation_date")
	t_creation_date.text = str(appln.created)

	t_creation_place = ET.SubElement(term, "creation_place")

	t_source_reference = ET.SubElement(term, "source_reference")
	t_interpretation = ET.SubElement(term, "interpretation")
	t_normalized_representation = ET.SubElement(term, "normalized_representation")
	t_printed_representation = ET.SubElement(term, "printed_representation")
	#--------------------
	p_id = ET.SubElement(t_printed_representation, "id")
	p_creator = ET.SubElement(t_printed_representation, "creator")
	p_creator.text = appln.createdBy.username

	p_creation_date = ET.SubElement(t_printed_representation, "creation_date")
	p_creation_date.text = str(appln.created)

	p_creation_place = ET.SubElement(t_printed_representation, "creation_place")

	p_source_reference = ET.SubElement(t_printed_representation, "source_reference")

	t_term_part = ET.SubElement(t_printed_representation, "term_part")
	#-------------------
	t_id = ET.SubElement(t_term_part, "id")
	t_creator = ET.SubElement(t_term_part, "creator")
	t_creator.text = appln.createdBy.username

	t_creation_date = ET.SubElement(t_term_part, "creation_date")
	t_creation_date.text = str(appln.created)

	t_creation_place = ET.SubElement(t_term_part, "creation_place")

	t_source_reference = ET.SubElement(t_term_part, "source_reference")
	t_expression = ET.SubElement(t_term_part, "expression")
	t_position = ET.SubElement(t_term_part, "position")
	t_normalization = ET.SubElement(t_term_part, "normalization")
	t_formatted_pointer = ET.SubElement(t_term_part, "formatted_pointer")
	t_format = ET.SubElement(t_term_part, "format")

	return root
	#indent(root)
	#quadruple = ET.dump(root)
	#return quadruple

#<term>
#	<id />
#	<creator>http://www.digitalhps.org/concepts/CON49f66a30-6e3c-44fc-9557-d87a2936e950</creator>
#	<creation_date>2002-05-30T09:00:00</creation_date>
#	<creation_place>http://www.digitalhps.org/concepts/WID-08769645-N-??-berlin</creation_place>
#	<source_reference>http://www.digitalhps.org/concepts/CONda66ba9a-04d4-4f26-ae58-22132212bf66</source_reference>
#	<interpretation>URI1</interpretation>
#	<normalized_representation>URI2</normalized_representation>
#	<printed_representation>
#		<creator>http://www.digitalhps.org/concepts/CON49f66a30-6e3c-44fc-9557-d87a2936e950</creator>
#		<creation_date>2002-05-30T09:00:00</creation_date>
#	<id></id>
	#	<creation_place>http://www.digitalhps.org/concepts/WID-08769645-N-??-berlin</creation_place>
#		<source_reference>http://www.digitalhps.org/concepts/CONda66ba9a-04d4-4f26-ae58-22132212bf66</source_reference>
#		<term_part>
#			<id></id>
#			<creator>http://www.digitalhps.org/concepts/CON49f66a30-6e3c-44fc-9557-d87a2936e950</creator>
#			<creation_date>2002-05-30T09:00:00</creation_date>
##			<creation_place>http://www.digitalhps.org/concepts/WID-08769645-N-??-berlin</creation_place>
#			<source_reference>http://www.digitalhps.org/concepts/CONda66ba9a-04d4-4f26-ae58-22132212bf66</source_reference>
#			<expression>Exp1</expression>
##			<position>1</position>
#			<normalization>URI1</normalization>
#			<formatted_pointer>Pointer1</formatted_pointer>
#			<format>Format1</format>
#		</term_part>
#	<certain>true</certain>
#	<referenced_terms>
###	</printed_representation>

rel = Relation.objects.all()[0]
appln = Appellation.objects.filter(id = rel.createdBy_id)[0]

#print rel.__dict__
#print appln.__dict__

xml = create_relation(rel)
indent(xml)
quad = ET.dump(xml)


#print create_appellation(appln)
