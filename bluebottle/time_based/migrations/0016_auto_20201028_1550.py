# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-28 14:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0015_auto_20201028_1546'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='duration',
            name='duration_period',
        ),
        migrations.AddField(
            model_name='duration',
            name='period',
            field=models.CharField(blank=True, choices=[('overall', 'overall'), ('day', 'per day'), ('week', 'per week'), ('month', 'per month')], max_length=20, null=True, verbose_name='period'),
        ),
    ]
