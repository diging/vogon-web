# Generated by Django 2.2 on 2022-02-02 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0040_vogonuser_is_password_reset_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='vogonuser',
            name='is_reset_password_required',
            field=models.BooleanField(default=False),
        ),
    ]
