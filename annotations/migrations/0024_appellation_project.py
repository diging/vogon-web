# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0023_relationset_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='appellation',
            name='project',
            field=models.ForeignKey(related_name='appellations', blank=True, to='annotations.TextCollection', null=True, on_delete=models.CASCADE),
        ),
    ]
