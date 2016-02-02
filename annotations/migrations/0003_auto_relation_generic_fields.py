# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations


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
    have = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9")#[0]#, defaults={'real_type_id': conceptType.id})[0]
    be = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316")#[0]#, defaults={'real_type_id': conceptType.id})[0]

    appellationType = ContentType.objects.get_for_model(Appellation)
    relationType = ContentType.objects.get_for_model(Relation)

    for relation in Relation.objects.all():
        relationSet = RelationSet(
            createdBy_id = 1,
        )
        relationSet.save()
        # Need to look at the controlling_verb, and if set create nested
        #  Relations accordingly.
        if relation.predicate.controlling_verb:
            # Create baseless appellations for have and be.
            haveAppellation = Appellation(
                occursIn = relation.occursIn,
                createdBy_id = 1,
            )
            haveAppellation.interpretation = have
            haveAppellation.save()
            beAppellation = Appellation(
                occursIn = relation.occursIn,
                createdBy_id = 1,
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
                    createdBy_id = 1,
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
                    createdBy_id = 1,
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
        ('annotations', '0002_auto_20160128_1717'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='RelationTemplatePart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('internal_id', models.IntegerField(default=-1)),
                ('source_node_type', models.CharField(blank=True, max_length=2, null=True, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'RE', b'Relation')])),
                ('source_relationtemplate_internal_id', models.IntegerField(default=-1)),
                ('source_prompt_text', models.BooleanField(default=True)),
                ('source_description', models.TextField(null=True, blank=True)),
                ('predicate_node_type', models.CharField(blank=True, max_length=2, null=True, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'IS', b'Is/was'), (b'HA', b'Has/had')])),
                ('predicate_prompt_text', models.BooleanField(default=True)),
                ('predicate_description', models.TextField(null=True, blank=True)),
                ('object_node_type', models.CharField(blank=True, max_length=2, null=True, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'RE', b'Relation')])),
                ('object_relationtemplate_internal_id', models.IntegerField(default=-1)),
                ('object_prompt_text', models.BooleanField(default=True)),
                ('object_description', models.TextField(null=True, blank=True)),
                ('object_concept', models.ForeignKey(related_name='used_as_concept_for_object', blank=True, to='concepts.Concept', null=True)),
                ('object_relationtemplate', models.ForeignKey(related_name='used_as_object', blank=True, to='annotations.RelationTemplatePart', null=True)),
                ('object_type', models.ForeignKey(related_name='used_as_type_for_object', blank=True, to='concepts.Type', null=True)),
                ('part_of', models.ForeignKey(related_name='template_parts', to='annotations.RelationTemplate')),
                ('predicate_concept', models.ForeignKey(related_name='used_as_concept_for_predicate', blank=True, to='concepts.Concept', null=True)),
                ('predicate_type', models.ForeignKey(related_name='used_as_type_for_predicate', blank=True, to='concepts.Type', null=True)),
                ('source_concept', models.ForeignKey(related_name='used_as_concept_for_source', blank=True, to='concepts.Concept', null=True)),
                ('source_relationtemplate', models.ForeignKey(related_name='used_as_source', blank=True, to='annotations.RelationTemplatePart', null=True)),
                ('source_type', models.ForeignKey(related_name='used_as_type_for_source', blank=True, to='concepts.Type', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='relation',
            name='object_content_type',
            field=models.ForeignKey(related_name='as_object_in_relation', blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='relation',
            name='object_object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relation',
            name='source_content_type',
            field=models.ForeignKey(related_name='as_source_in_relation', blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='relation',
            name='source_object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.CreateModel(
            name='RelationSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('createdBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(related_name='instantiations', blank=True, to='annotations.RelationTemplate', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='relation',
            name='part_of',
            field=models.ForeignKey(related_name='constituents', blank=True, to='annotations.RelationSet', null=True),
        ),
        migrations.RunPython(
            populate_relation_generic_fields,
            populate_relation_generic_fields_reverse
        ),
        migrations.RemoveField(
            model_name='relation',
            name='object',
        ),
        migrations.RemoveField(
            model_name='relation',
            name='source',
        ),
    ]
