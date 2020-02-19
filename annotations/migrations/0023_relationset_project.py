# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0022_text_part_of'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='project',
            field=models.ForeignKey(related_name='relationsets', blank=True, to='annotations.TextCollection', null=True, on_delete=models.CASCADE),
        ),
    ]
