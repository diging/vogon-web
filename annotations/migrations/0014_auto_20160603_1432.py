# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0013_relationset_pending'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='nominated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='relationset',
            name='nominatedOn',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
