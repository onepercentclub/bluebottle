# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-02-09 08:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0027_auto_20201229_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiativeplatformsettings',
            name='enable_multiple_dates',
            field=models.BooleanField(default=False),
        ),
    ]
