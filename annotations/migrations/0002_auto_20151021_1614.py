# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='source',
            field=models.ForeignKey(related_name='loadedTexts', blank=True, to='annotations.Repository', null=True),
        ),
    ]
