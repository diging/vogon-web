# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0021_text_content_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='part_of',
            field=models.ForeignKey(related_name='parts', blank=True, to='annotations.Text', null=True),
        ),
    ]
