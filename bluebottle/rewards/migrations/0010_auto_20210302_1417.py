# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 13:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0012_auto_20210302_1417'),
        ('rewards', '0009_auto_20191104_1230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reward',
            name='project',
        ),
        migrations.DeleteModel(
            name='Reward',
        ),
    ]
