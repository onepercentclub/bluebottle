# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-12-07 10:37
from __future__ import unicode_literals

from django.db import migrations

def update_stat_types(apps, schema_editor):
    DatabaseStatistic = apps.get_model('statistics', 'DatabaseStatistic')

    DatabaseStatistic.objects.filter(
        query__in=('events_succeeded', 'assignments_succeeded')
    ).update(query='time_activities_succeeded')

    DatabaseStatistic.objects.filter(
        query__in=('events_online', 'assignments_online')
    ).update(query='time_activities_online')

    DatabaseStatistic.objects.filter(
        query__in=('event_members', 'assignments_members')
    ).update(query='activity_participants')


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0012_auto_20200812_1024'),
    ]

    operations = [
        migrations.RunPython(update_stat_types)
    ]
