# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0010_auto_20160304_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='DateAppellation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('year', models.PositiveIntegerField(default=1)),
                ('month', models.IntegerField(default=0)),
                ('day', models.IntegerField(default=0)),
                ('createdBy', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('occursIn', models.ForeignKey(to='annotations.Text', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
