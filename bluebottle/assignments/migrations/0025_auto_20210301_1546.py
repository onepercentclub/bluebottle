# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-01 14:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0038_auto_20210127_1358'),
        ('assignments', '0024_auto_20201112_1519'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicant',
            name='contributor_ptr',
        ),
        migrations.RemoveField(
            model_name='applicant',
            name='document',
        ),
        migrations.RemoveField(
            model_name='assignment',
            name='activity_ptr',
        ),
        migrations.RemoveField(
            model_name='assignment',
            name='expertise',
        ),
        migrations.RemoveField(
            model_name='assignment',
            name='location',
        ),
        migrations.DeleteModel(
            name='Applicant',
        ),
        migrations.DeleteModel(
            name='Assignment',
        ),
    ]
