# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0008_relationset_occursin'),
    ]

    operations = [
        migrations.AddField(
            model_name='vogonuser',
            name='imagefile',
            field=models.URLField(null=True, blank=True),
        ),
    ]
