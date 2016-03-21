# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='concept',
            name='merged_with',
            field=models.ForeignKey(related_name='merged_concepts', blank=True, to='concepts.Concept', null=True),
        ),
    ]
