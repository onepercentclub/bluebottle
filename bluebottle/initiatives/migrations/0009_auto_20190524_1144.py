# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-24 09:44
from __future__ import unicode_literals

import bluebottle.files.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0008_auto_20190513_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiative',
            name='place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.Geolocation'),
        )
    ]
