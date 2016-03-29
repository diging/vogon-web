# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def fake(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0008_relationset_occursin'),
    ]

    operations = [
        migrations.RunPython(fake, fake),
        # migrations.AddField(
        #     model_name='vogonuser',
        #     name='imagefile',
        #     field=models.FileField(default=b'', null=True, upload_to=b'uploads/', blank=True),
        # ),
    ]
