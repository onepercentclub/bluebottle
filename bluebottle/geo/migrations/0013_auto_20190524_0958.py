# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-24 07:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0012_auto_20190522_1341'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ActivityPlace',
            new_name='Geolocation',
        ),
    ]
