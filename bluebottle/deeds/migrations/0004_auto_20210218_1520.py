# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-02-18 14:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0003_auto_20210218_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deed',
            name='end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='deed',
            name='start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
