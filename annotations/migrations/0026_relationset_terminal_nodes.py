# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0002_concept_merged_with'),
        ('annotations', '0025_relationset_representation'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='terminal_nodes',
            field=models.ManyToManyField(to='concepts.Concept'),
        ),
    ]
