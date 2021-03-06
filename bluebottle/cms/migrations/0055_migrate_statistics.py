# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-08 06:50
from __future__ import unicode_literals

from django.db import migrations


TYPE_MAP = {
    'projects_realized': 'activities_succeeded',
    'projects_complete': 'activities_succeeded',
    'tasks_realized': 'assignments_succeeded',
    'task_members': 'activity_members',
    'projects_online': 'activities_online',
}


def migrate_statistics(apps, schema_editor):
    Stat = apps.get_model('cms', 'Stat')

    for stat in Stat.objects.all():
        stat.type = TYPE_MAP.get(stat.type, stat.type)

        stat.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0054_auto_20171031_1428_squashed_0068_migrate_start_project'),
    ]

    operations = [
        migrations.RunPython(migrate_statistics),
    ]
