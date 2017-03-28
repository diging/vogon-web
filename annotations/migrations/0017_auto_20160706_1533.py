# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0016_add_documentposition_to_appellations'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='document_location',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='text',
            name='document_type',
            field=models.CharField(blank=True, max_length=2, null=True, choices=[(b'PT', b'Plain text'), (b'IM', b'Image'), (b'HP', b'Hypertext')]),
        ),
    ]
