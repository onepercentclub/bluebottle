# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-05 19:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0006_auto_20161205_1956'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stat',
            old_name='name',
            new_name='title',
        ),
    ]
