# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='title',
            field=models.CharField(max_length=1000),
        ),
    ]
