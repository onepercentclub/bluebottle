# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-19 12:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0025_memberplatformsettings_consent_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='last_logout',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last Logout'),
        ),
    ]
