# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-11-29 10:32
from __future__ import unicode_literals

from django.db import migrations


ACTIVITY_SEARCH_FILTERS = (
    'location', 'country', 'date', 'skill', 'type', 'theme', 'category', 'status',
)
INITIATIVE_SEARCH_FILTERS = (
    'location', 'country', 'theme', 'category',
)


def set_search_filters(apps, schema_editor):
    InitiativePlatformSettings = apps.get_model("initiatives", "InitiativePlatformSettings")

    settings = InitiativePlatformSettings.objects.get()

    settings.activity_search_filters = [
        'country' if filter == 'location' else filter for filter in settings.search_filters
        if filter in ACTIVITY_SEARCH_FILTERS
    ]
    settings.initiative_search_filters = [
        'country' if filter == 'location' else filter for filter in settings.search_filters
        if filter in INITIATIVE_SEARCH_FILTERS
    ]

    settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0020_auto_20191129_1131'),
    ]

    operations = [
        migrations.RunPython(set_search_filters)
    ]
