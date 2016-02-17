# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255, null=True, blank=True)),
                ('uri', models.CharField(unique=True, max_length=255)),
                ('resolved', models.BooleanField(default=False)),
                ('description', models.TextField(null=True, blank=True)),
                ('authority', models.CharField(max_length=255)),
                ('pos', models.CharField(max_length=255, null=True, blank=True)),
                ('concept_state', models.CharField(default=b'Pending', max_length=10, choices=[(b'Pending', b'Pending'), (b'Rejected', b'Rejected'), (b'Approved', b'Approved'), (b'Resolved', b'Resolved')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('concept_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='concepts.Concept')),
            ],
            options={
                'abstract': False,
            },
            bases=('concepts.concept',),
        ),
        migrations.AddField(
            model_name='concept',
            name='real_type',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='concept',
            name='typed',
            field=models.ForeignKey(related_name='instances', blank=True, to='concepts.Type', null=True),
        ),
    ]
