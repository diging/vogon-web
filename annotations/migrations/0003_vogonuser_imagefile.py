# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20160128_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='vogonuser',
            name='imagefile',
            field=models.FileField(default=b'', null=True, upload_to=b'uploads/', blank=True),
        ),
    ]
