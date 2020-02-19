# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0006_auto_20160202_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtemplate',
            name='expression',
            field=models.TextField(null=True),
        ),
    ]
