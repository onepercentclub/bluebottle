# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-01-29 09:50
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
            name='is_anonymized',
            field=models.BooleanField(default=False, verbose_name='Is anonymized'),
        ),
    ]
