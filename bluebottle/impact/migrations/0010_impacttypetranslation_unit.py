# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-08-11 14:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0009_auto_20200810_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='impacttypetranslation',
            name='unit',
            field=models.CharField(blank=True, help_text='E.g. "liters" or "kg"', max_length=100, null=True, verbose_name='unit'),
        ),
    ]
