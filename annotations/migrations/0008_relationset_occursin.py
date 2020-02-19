# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0007_relationtemplate_expression'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationset',
            name='occursIn',
            field=models.ForeignKey(related_name='relationsets', default=1, to='annotations.Text', on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
