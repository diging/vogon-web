# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0013_relationset_pending'),
    ]

    operations = [
        migrations.AddField(
            model_name='textcollection',
            name='quadriga_id',
            field=models.CharField(help_text=b'\n    Use this field to specify the ID of an existing project in Quadriga with\n    which this project should be associated.', max_length=255, null=True, blank=True),
        ),
    ]
