# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-04-15 06:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0025_auto_20210414_1508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='geolocation',
            name='old_position',
        ),
        migrations.RemoveField(
            model_name='location',
            name='old_position',
        ),
        migrations.RemoveField(
            model_name='place',
            name='old_position',
        ),
    ]
