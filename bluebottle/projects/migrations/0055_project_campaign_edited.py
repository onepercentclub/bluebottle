# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-11-22 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0054_auto_20171122_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='campaign_edited',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Campaign edited'),
        ),
    ]
