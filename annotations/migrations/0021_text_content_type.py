# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0020_text_repository_source_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='content_type',
            field=models.CharField(default='text/plain', max_length=255),
            preserve_default=False,
        ),
    ]
