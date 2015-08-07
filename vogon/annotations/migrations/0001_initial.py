# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import annotations.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('concepts', '__first__'),
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
            ],
            options={
                'abstract': False,
            },
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
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('createdBy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
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
                ('addedBy', models.ForeignKey(related_name='addedTexts', to=settings.AUTH_USER_MODEL)),
                ('source', models.ForeignKey(related_name='loadedTexts', to='annotations.Repository')),
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
            name='inSession',
            field=models.ForeignKey(to='annotations.Session'),
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
            model_name='appellation',
            name='inSession',
            field=models.ForeignKey(to='annotations.Session'),
        ),
        migrations.AddField(
            model_name='appellation',
            name='interpretation',
            field=models.ForeignKey(to='concepts.Concept'),
        ),
        migrations.AddField(
            model_name='appellation',
            name='occursIn',
            field=models.ForeignKey(to='annotations.Text'),
        ),
    ]
