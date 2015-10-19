# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import annotations.models


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
            ],
            options={
                'abstract': False,
            },
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
                ('source', models.ForeignKey(related_name='loadedTexts', blank=True, to='annotations.Repository')),
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
                ('texts', models.ManyToManyField(related_name='partOf', null=True, to='annotations.Text', blank=True)),
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
            name='object',
            field=models.ForeignKey(related_name='relationsTo', to='annotations.Appellation'),
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
            name='source',
            field=models.ForeignKey(related_name='relationsFrom', to='annotations.Appellation'),
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
