# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0004_auto_20160202_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtemplate',
            name='expression',
            field=models.TextField(null=True),
        ),
    ]
