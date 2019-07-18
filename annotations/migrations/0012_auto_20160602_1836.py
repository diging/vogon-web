# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0011_dateappellation'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuadrigaAccession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('project_id', models.CharField(max_length=255, null=True, blank=True)),
                ('workspace_id', models.CharField(max_length=255, null=True, blank=True)),
                ('network_id', models.CharField(max_length=255, null=True, blank=True)),
                ('createdBy', models.ForeignKey(related_name='accessions', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='appellation',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='appellation',
            name='submittedOn',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dateappellation',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dateappellation',
            name='submittedOn',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relation',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='relation',
            name='submittedOn',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='relationset',
            name='submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='relationset',
            name='submittedOn',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='appellation',
            name='submittedWith',
            field=models.ForeignKey(blank=True, to='annotations.QuadrigaAccession', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='dateappellation',
            name='submittedWith',
            field=models.ForeignKey(blank=True, to='annotations.QuadrigaAccession', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='relation',
            name='submittedWith',
            field=models.ForeignKey(blank=True, to='annotations.QuadrigaAccession', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='relationset',
            name='submittedWith',
            field=models.ForeignKey(blank=True, to='annotations.QuadrigaAccession', null=True, on_delete=models.CASCADE),
        ),
    ]
