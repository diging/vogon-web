# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0026_relationset_terminal_nodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtemplate',
            name='_terminal_nodes',
            field=models.TextField(null=True, blank=True),
        ),
    ]
