# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-01-15 15:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0034_auto_20200114_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberplatformsettings',
            name='background',
            field=models.ImageField(blank=True, null=True, upload_to=b'site_content/'),
        ),
    ]
