# Generated by Django 2.2 on 2021-04-05 17:11

from django.conf import settings
from django.db import migrations, models
from django.db.models import F
import django.db.models.deletion

def copy_owner_to_created_by(apps, schema_editor):
    TextCollection = apps.get_model('annotations', 'textcollection')
    db_alias = schema_editor.connection.alias
    TextCollection.objects.using(db_alias).all().update(
        createdBy=F('ownedBy')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0038_auto_20200803_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='textcollection',
            name='createdBy',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='projects_created', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.RunPython(copy_owner_to_created_by),
    ]
    atomic = False
