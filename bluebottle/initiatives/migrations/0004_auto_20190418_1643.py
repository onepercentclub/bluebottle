# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-18 14:43
from __future__ import unicode_literals

import bluebottle.files.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0003_auto_20190403_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='initiative',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
