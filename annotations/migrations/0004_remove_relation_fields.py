# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations

class Migration(migrations.Migration):
    dependencies = [
        ('annotations', '0003_auto_relation_generic_fields'),
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
