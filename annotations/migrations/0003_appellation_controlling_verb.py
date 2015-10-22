# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20151021_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='appellation',
            name='controlling_verb',
            field=models.CharField(blank=True, max_length=4, null=True, help_text=b'\n    Applies only if the Appellation is a predicate.', choices=[(None, b''), (b'is', b'is/was'), (b'has', b'has/had')]),
        ),
    ]
