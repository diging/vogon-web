# -*- coding: utf-8 -*-


from django.db import models, migrations


def populate_position(apps, schema_editor):
    Appellation = apps.get_model("annotations", "Appellation")
    DocumentPosition = apps.get_model("annotations", "DocumentPosition")

    for appellation in Appellation.objects.filter(position=None):
        appellation.position = DocumentPosition.objects.create(
            occursIn_id=appellation.occursIn.id,
            position_type='TI',
            position_value=appellation.tokenIds)
        appellation.save()


def depopulate_position(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0015_auto_20160623_1327'),
    ]

    operations = [
        migrations.RunPython(
            populate_position,
            depopulate_position,
        ),
    ]
