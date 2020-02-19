# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0005_relation_remove_source_and_object'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtemplatepart',
            name='object_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relationtemplatepart',
            name='predicate_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relationtemplatepart',
            name='source_label',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
