# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-24 14:00
from __future__ import unicode_literals

from django.db import migrations


def migrate_site_platform_settings(apps, schema_editor):
    SitePlatformSettings = apps.get_model('cms', 'SitePlatformSettings')
    site_setttings, _ = SitePlatformSettings.objects.get_or_create()
    site_setttings.save()


def dummy(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0024_siteplatformsettings'),
    ]

    operations = [
        migrations.RunPython(migrate_site_platform_settings, dummy)
    ]
