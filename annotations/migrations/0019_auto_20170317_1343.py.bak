# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
        ('annotations', '0018_auto_20160706_1533'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='text',
            options={},
        ),
        migrations.AddField(
            model_name='text',
            name='repository',
            field=models.ForeignKey(related_name='texts', blank=True, to='repository.Repository', null=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='uri',
            field=models.CharField(help_text=b'Uniform Resource Identifier. This should be sufficient to retrieve text from a repository.', unique=True, max_length=255),
        ),
    ]
