# Generated by Django 2.2 on 2023-04-07 21:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goat', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authority',
            name='configuration',
        ),
    ]