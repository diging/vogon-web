# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0014_textcollection_quadriga_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentPosition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position_type', models.CharField(max_length=2, choices=[(b'TI', b'Token IDs'), (b'BB', b'Bounding box'), (b'XP', b'XPath'), (b'CO', b'Character offsets'), (b'WD', b'Whole document')])),
                ('position_value', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='appellation',
            name='controlling_verb',
            field=models.CharField(blank=True, max_length=4, null=True, choices=[(None, b''), (b'is', b'is/was'), (b'has', b'has/had')]),
        ),
        migrations.AlterField(
            model_name='text',
            name='created',
            field=models.DateField(help_text=b'The publication or creation date of the original document.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='title',
            field=models.CharField(help_text=b'The original title of the document.', max_length=1000),
        ),
        migrations.AlterField(
            model_name='text',
            name='uri',
            field=models.CharField(help_text=b' Uniform Resource Identifier. This should be sufficient to retrieve text from a repository. ', unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='textcollection',
            name='quadriga_id',
            field=models.CharField(help_text=b'Use this field to specify the ID of an existing project in Quadriga with which this project should be associated.', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='affiliation',
            field=models.CharField(help_text=b'Your home institution or employer.', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='conceptpower_uri',
            field=models.URLField(help_text=b'Advanced: if you have an entry for yourself in the Conceptpower authority service, please enter it here.', max_length=500, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='imagefile',
            field=models.URLField(help_text=b'Upload a profile picture.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='is_active',
            field=models.BooleanField(default=True, help_text=b'Un-set this field to deactivate a user. This is extremely preferable to deletion.'),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='link',
            field=models.URLField(help_text=b'The location of your online bio or homepage.', max_length=500, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='vogonuser',
            name='location',
            field=models.CharField(help_text=b'Your current geographical location.', max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='documentposition',
            name='occursIn',
            field=models.ForeignKey(related_name='positions', to='annotations.Text'),
        ),
        migrations.AddField(
            model_name='appellation',
            name='position',
            field=models.ForeignKey(related_name='appellations', blank=True, to='annotations.DocumentPosition', null=True),
        ),
    ]
