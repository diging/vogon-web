# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0005_auto_20160215_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vogonuser',
            name='imagefile',
            field=models.FileField(default=b'', null=True, upload_to=b'/', blank=True),
        ),
    ]
