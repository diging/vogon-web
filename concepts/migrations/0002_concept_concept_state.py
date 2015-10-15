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
            name='concept_state',
            field=models.CharField(default=b'Pending', max_length=10, choices=[(b'Pending', b'Pending'), (b'Rejected', b'Rejected'), (b'Approved', b'Approved'), (b'Resolved', b'Resolved')]),
        ),
    ]
