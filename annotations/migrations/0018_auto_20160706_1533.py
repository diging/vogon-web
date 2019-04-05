# -*- coding: utf-8 -*-


from django.db import models, migrations


def populate_document_type(apps, schema_editor):
    Text = apps.get_model("annotations", "Text")
    Text.objects.exclude(tokenizedContent='').update(document_type='PT')


def populate_document_type_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0017_auto_20160706_1533'),
    ]

    operations = [
        migrations.RunPython(
            populate_document_type,
            populate_document_type_reverse
        )
    ]
