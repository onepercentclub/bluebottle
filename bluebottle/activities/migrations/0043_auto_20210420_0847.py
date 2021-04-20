# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-04-20 06:47
from __future__ import unicode_literals

from django.db import migrations, connection


def create_activity_view(apps, schema_editor):
    sql = """
        DROP VIEW IF EXISTS activities;
        CREATE VIEW activities AS
            SELECT ct.model::text AS activity_type,
            ac.title,
            ac.id,
            ac.status,
            ac.created,
            ac.updated
        FROM {0}.activities_activity ac
            LEFT JOIN {0}.time_based_dateactivity da ON da.timebasedactivity_ptr_id = ac.id
            LEFT JOIN {0}.time_based_periodactivity pa ON pa.timebasedactivity_ptr_id = ac.id
            LEFT JOIN {0}.funding_funding fu ON fu.activity_ptr_id = ac.id
            LEFT JOIN {0}.deeds_deed de ON de.activity_ptr_id = ac.id
            JOIN {0}.django_content_type ct ON ac.polymorphic_ctype_id = ct.id;
    """.format(connection.tenant.schema_name)

    if connection.tenant.schema_name != 'public':
        schema_editor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0042_effortcontribution_contribution_type'),
    ]

    operations = [
        migrations.RunPython(create_activity_view, migrations.RunPython.noop)
    ]
