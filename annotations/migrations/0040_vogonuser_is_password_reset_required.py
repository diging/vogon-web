# Generated by Django 2.2 on 2022-01-28 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0039_textcollection_createdby'),
    ]

    operations = [
        migrations.AddField(
            model_name='vogonuser',
            name='is_password_reset_required',
            field=models.BooleanField(default=False),
        ),
    ]
