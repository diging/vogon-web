# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0024_appellation_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='representation',
            field=models.TextField(null=True, blank=True),
        ),
    ]
