# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0012_auto_20160602_1836'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='pending',
            field=models.BooleanField(default=False),
        ),
    ]
