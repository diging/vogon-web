# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('concepts', '__first__'),
        ('annotations', '0004_relation_data_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='relation',
            name='object',
        ),
        migrations.RemoveField(
            model_name='relation',
            name='source',
        ),
    ]
