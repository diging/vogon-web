# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0003_auto_relation_generic_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtemplatepart',
            name='object_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relationtemplatepart',
            name='predicate_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relationtemplatepart',
            name='source_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
