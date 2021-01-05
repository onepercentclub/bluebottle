# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-28 08:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0010_auto_20201027_1652'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributionduration',
            name='duration',
        ),

        migrations.AddField(
            model_name='contributionduration',
            name='duration',
            field=models.DurationField(blank=True, null=True, verbose_name='duration'),
        ),
    ]
