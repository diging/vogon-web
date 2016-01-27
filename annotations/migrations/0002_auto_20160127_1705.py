# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.db import models, migrations


def populate_relation_generic_fields(apps, schema_editor):
    Relation = apps.get_model("annotations", "Relation")
    for relation in Relation.objects.all():
        relation.source_content_object = relation.source
        relation.object_content_object = relation.object
        print relation
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
        ('annotations', '0001_initial'),
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
