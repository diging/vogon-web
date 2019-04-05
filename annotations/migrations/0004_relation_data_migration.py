# -*- coding: utf-8 -*-

from django.db import models, migrations
from django.conf import settings


def populate_relation_generic_fields(apps, schema_editor):
    """
    Move old references to Appellations in Relation.source and Relation.object
    to new GenericForeignKey fields on Relation.
    """

    Relation = apps.get_model("annotations", "Relation")
    RelationSet = apps.get_model("annotations", "RelationSet")
    Appellation = apps.get_model("annotations", "Appellation")
    Concept = apps.get_model("concepts", "Concept")
    ContentType = apps.get_model('contenttypes', 'ContentType')
    conceptType = ContentType.objects.get_for_model(Concept)
    try:
        have = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9")#[0]#, defaults={'real_type_id': conceptType.id})[0]
    except Concept.DoesNotExist:
        have = Concept(uri="http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9", authority='Conceptpower', real_type=conceptType)
        have.save()
    try:
        be = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316")#[0]#, defaults={'real_type_id': conceptType.id})[0]
    except Concept.DoesNotExist:
        be = Concept(uri="http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316", authority='Conceptpower', real_type=conceptType)
        be.save()

    appellationType = ContentType.objects.get_for_model(Appellation)
    relationType = ContentType.objects.get_for_model(Relation)

    for relation in Relation.objects.all():
        relationSet = RelationSet(
            createdBy_id = relation.createdBy.id,
            occursIn = relation.occursIn,
        )
        relationSet.save()
        # Need to look at the controlling_verb, and if set create nested
        #  Relations accordingly.
        if relation.predicate.controlling_verb:
            # Create baseless appellations for have and be.
            haveAppellation = Appellation(
                occursIn = relation.occursIn,
                createdBy_id = relation.createdBy.id,
                asPredicate = True,
            )
            haveAppellation.interpretation = have
            haveAppellation.save()
            beAppellation = Appellation(
                occursIn = relation.occursIn,
                createdBy_id = relation.createdBy.id,
                asPredicate = True,
            )
            beAppellation.interpretation = be
            beAppellation.save()

            if relation.predicate.controlling_verb == 'has':
                downRelation = Relation(
                    source_content_type = appellationType,
                    source_object_id = relation.predicate.id,
                    source = relation.predicate,
                    predicate = beAppellation,
                    object_content_type = appellationType,
                    object_object_id = relation.object.id,
                    object = relation.object,
                    createdBy_id = relation.createdBy.id,
                    occursIn = relation.occursIn,
                    part_of = relationSet,
                )
                downRelation.save()

                relation.source_content_type = appellationType
                relation.source_object_id = relation.source.id
                relation.predicate = haveAppellation
                relation.object_content_type  = relationType
                relation.object_object_id = downRelation.id
                relation.part_of = relationSet
            elif relation.predicate.controlling_verb == 'is':
                upRelation = Relation(
                    source_content_type = appellationType,
                    source_object_id = relation.object.id,
                    source = relation.object,
                    predicate = haveAppellation,
                    object_content_type = relationType,
                    object_object_id = relation.id,
                    object = relation.object,
                    occursIn = relation.occursIn,
                    createdBy_id = relation.createdBy.id,
                    part_of = relationSet,
                )
                upRelation.save()

                relation.source_content_type = appellationType
                relation.source_object_id = relation.predicate.id
                relation.predicate = beAppellation
                relation.object_content_type = appellationType
                relation.object_object_id = relation.source.id
                relation.part_of = relationSet

        else:   # No nesting, just migrate source/object data to new fields.
            relation.source_content_type = appellationType
            relation.object_content_type = appellationType
            relation.source_object_id = relation.source.id
            relation.object_object_id = relation.object.id
            relation.part_of = relationSet
            relation.save()

        relation.save()


def populate_relation_generic_fields_reverse(apps, schema_editor):
    Relation = apps.get_model("annotations", "Relation")
    for relation in Relation.objects.all():
        relation.source = relation.source_content_object
        relation.object = relation.object_content_object
        relation.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('concepts', '__first__'),
        ('annotations', '0003_auto_relation_generic_fields'),
    ]

    operations = [
        migrations.RunPython(
            populate_relation_generic_fields,
            populate_relation_generic_fields_reverse
        ),
    ]
