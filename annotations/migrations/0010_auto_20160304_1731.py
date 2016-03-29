# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def fake(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0009_vogonuser_imagefile'),
    ]

    operations = [
        migrations.RunPython(fake, fake),
        # migrations.AlterField(
        #     model_name='vogonuser',
        #     name='imagefile',
        #     field=models.URLField(null=True, blank=True),
        # ),
    ]
