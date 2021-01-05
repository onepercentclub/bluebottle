# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-27 15:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0009_auto_20201026_1435'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='onadateactivity',
            name='duration',
        ),

        migrations.AddField(
            model_name='onadateactivity',
            name='duration',
            field=models.DurationField(blank=True, null=True, verbose_name='duration'),
        ),
    ]
