# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-01-29 08:51
from __future__ import unicode_literals

from django.db import migrations, connection


def migrate_location_to_period(apps, schema_editor):
    period_sql = """
    UPDATE {0}.time_based_periodactivity as pa
        SET location_id=tb.location_id,
            location_hint=tb.location_hint,
            is_online=tb.is_online
        FROM {0}.time_based_timebasedactivity tb
        WHERE pa.timebasedactivity_ptr_id = tb.activity_ptr_id
    """.format(connection.tenant.schema_name)

    if connection.tenant.schema_name != 'public':
        schema_editor.execute(period_sql)


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0055_auto_20210129_0951'),
    ]

    operations = [
        migrations.RunPython(
            migrate_location_to_period,
            migrations.RunPython.noop
        )
    ]
