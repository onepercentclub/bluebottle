# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-29 06:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignment',
            old_name='end',
            new_name='deadline',
        ),
    ]
