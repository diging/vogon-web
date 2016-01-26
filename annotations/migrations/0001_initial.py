# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import annotations.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
        ('concepts', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='VogonUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(unique=True, max_length=255)),
                ('email', models.EmailField(max_length=255, verbose_name=b'email address')),
                ('affiliation', models.CharField(max_length=255, null=True, blank=True)),
                ('location', models.CharField(max_length=255, null=True, blank=True)),
                ('link', models.URLField(max_length=500, null=True, blank=True)),
                ('full_name', models.CharField(max_length=255, null=True, blank=True)),
                ('conceptpower_uri', models.URLField(max_length=500, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Appellation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('tokenIds', models.TextField()),
                ('stringRep', models.TextField()),
                ('startPos', models.IntegerField(null=True, blank=True)),
                ('endPos', models.IntegerField(null=True, blank=True)),
                ('asPredicate', models.BooleanField(default=False)),
                ('controlling_verb', models.CharField(blank=True, max_length=4, null=True, help_text=b'\n    Applies only if the Appellation is a predicate.', choices=[(None, b''), (b'is', b'is/was'), (b'has', b'has/had')])),
                ('createdBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('interpretation', models.ForeignKey(to='concepts.Concept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Authorization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access_token', models.CharField(max_length=255)),
                ('token_type', models.CharField(max_length=255)),
                ('lifetime', models.IntegerField(default=0)),
                ('refresh_token', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('source_object_id', models.PositiveIntegerField()),
                ('object_object_id', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
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
                ('source_node_type', models.CharField(max_length=2, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'RE', b'Relation')])),
                ('source_relationtemplate_internal_id', models.IntegerField(default=-1)),
                ('source_prompt_text', models.BooleanField(default=True)),
                ('source_description', models.TextField(null=True, blank=True)),
                ('predicate_node_type', models.CharField(max_length=2, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'IS', b'Is/was'), (b'HA', b'Has/had')])),
                ('predicate_prompt_text', models.BooleanField(default=True)),
                ('predicate_description', models.TextField(null=True, blank=True)),
                ('object_node_type', models.CharField(max_length=2, choices=[(b'TP', b'Concept type'), (b'CO', b'Specific concept'), (b'RE', b'Relation')])),
                ('object_relationtemplate_internal_id', models.IntegerField(default=-1)),
                ('object_prompt_text', models.BooleanField(default=True)),
                ('object_description', models.TextField(null=True, blank=True)),
                ('object_concept', models.ForeignKey(related_name='used_as_concept_for_object', blank=True, to='concepts.Concept', null=True)),
                ('object_relationtemplate', models.ForeignKey(related_name='used_as_object', blank=True, to='annotations.RelationTemplate', null=True)),
                ('object_type', models.ForeignKey(related_name='used_as_type_for_object', blank=True, to='concepts.Type', null=True)),
                ('part_of', models.ForeignKey(related_name='template_parts', to='annotations.RelationTemplate')),
                ('predicate_concept', models.ForeignKey(related_name='used_as_concept_for_predicate', blank=True, to='concepts.Concept', null=True)),
                ('predicate_type', models.ForeignKey(related_name='used_as_type_for_predicate', blank=True, to='concepts.Type', null=True)),
                ('source_concept', models.ForeignKey(related_name='used_as_concept_for_source', blank=True, to='concepts.Concept', null=True)),
                ('source_relationtemplate', models.ForeignKey(related_name='used_as_source', blank=True, to='annotations.RelationTemplate', null=True)),
                ('source_type', models.ForeignKey(related_name='used_as_type_for_source', blank=True, to='concepts.Type', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('manager', models.CharField(max_length=255, choices=[(b'JARSManager', b'JARS')])),
                ('endpoint', models.CharField(max_length=255)),
                ('oauth_client_id', models.CharField(max_length=255)),
                ('oauth_secret_key', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='TemporalBounds',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', annotations.models.TupleField(null=True, blank=True)),
                ('occur', annotations.models.TupleField(null=True, blank=True)),
                ('end', annotations.models.TupleField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.CharField(unique=True, max_length=255)),
                ('tokenizedContent', models.TextField()),
                ('title', models.CharField(max_length=255)),
                ('created', models.DateField(null=True, blank=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('originalResource', models.URLField(null=True, blank=True)),
                ('public', models.BooleanField(default=True)),
                ('addedBy', models.ForeignKey(related_name='addedTexts', to=settings.AUTH_USER_MODEL)),
                ('annotators', models.ManyToManyField(related_name='userTexts', to=settings.AUTH_USER_MODEL)),
                ('source', models.ForeignKey(related_name='loadedTexts', blank=True, to='annotations.Repository', null=True)),
            ],
            options={
                'permissions': (('view_text', 'View text'),),
            },
        ),
        migrations.CreateModel(
            name='TextCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('ownedBy', models.ForeignKey(related_name='collections', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(related_name='contributes_to', to=settings.AUTH_USER_MODEL)),
                ('texts', models.ManyToManyField(related_name='partOf', null=True, to='annotations.Text', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='VogonGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=80, verbose_name='name')),
                ('permissions', models.ManyToManyField(to='auth.Permission', verbose_name='permissions', blank=True)),
            ],
            options={
                'verbose_name': 'group',
                'verbose_name_plural': 'groups',
            },
            managers=[
                ('objects', annotations.models.GroupManager()),
            ],
        ),
        migrations.AddField(
            model_name='relation',
            name='bounds',
            field=models.ForeignKey(blank=True, to='annotations.TemporalBounds', null=True),
        ),
        migrations.AddField(
            model_name='relation',
            name='createdBy',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='relation',
            name='object_content_type',
            field=models.ForeignKey(related_name='as_object_in_relation', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='relation',
            name='occursIn',
            field=models.ForeignKey(to='annotations.Text'),
        ),
        migrations.AddField(
            model_name='relation',
            name='predicate',
            field=models.ForeignKey(related_name='relationsAs', to='annotations.Appellation'),
        ),
        migrations.AddField(
            model_name='relation',
            name='source_content_type',
            field=models.ForeignKey(related_name='as_source_in_relation', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='authorization',
            name='repository',
            field=models.ForeignKey(to='annotations.Repository'),
        ),
        migrations.AddField(
            model_name='authorization',
            name='user',
            field=models.ForeignKey(related_name='authorizations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appellation',
            name='occursIn',
            field=models.ForeignKey(to='annotations.Text'),
        ),
    ]
