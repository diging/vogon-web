# Generated by Django 2.2 on 2022-03-25 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0039_textcollection_createdby'),
    ]

    operations = [
        migrations.AddField(
            model_name='vogonuser',
            name='is_token_reset_required',
            field=models.BooleanField(default=False),
        ),
    ]