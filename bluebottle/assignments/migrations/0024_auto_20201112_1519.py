# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-12 14:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0023_auto_20201112_1449'),
    ]

    operations = [
        migrations.RenameField(
            model_name='applicant',
            old_name='contribution_ptr',
            new_name='contributor_ptr',
        ),
    ]
