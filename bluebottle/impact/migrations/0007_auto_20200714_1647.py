# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-07-14 14:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0006_auto_20200710_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='impactgoal',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='impact.ImpactType', verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='impacttypetranslation',
            name='unit',
            field=models.CharField(blank=True, help_text='E.g. "liters" or "kg"', max_length=100, null=True, verbose_name='unit'),
        ),
    ]
