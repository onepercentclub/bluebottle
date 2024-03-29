# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-01-14 09:56
from __future__ import unicode_literals

from django.db import migrations, connection

from bluebottle.utils.utils import update_group_permissions

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            'Staff': {
                'perms': (
                    'add_dateactivityslot', 'change_dateactivityslot', 'delete_dateactivityslot',
                    'add_periodactivityslot', 'change_periodactivityslot', 'delete_periodactivityslot',
                )
            },
            'Anonymous': {
                'perms': (
                    'api_read_dateactivityslot',
                    'api_read_periodactivityslot',
                ) if not properties.CLOSED_SITE else ()
            },
            'Authenticated': {
                'perms': (
                    'api_read_dateactivityslot', 'api_add_own_dateactivityslot',
                    'api_change_own_dateactivityslot', 'api_delete_own_dateactivityslot',
                    'api_read_periodactivityslot', 'api_add_own_periodactivityslot',
                    'api_change_own_periodactivityslot', 'api_delete_own_periodactivityslot',
                )
            }
    }

    update_group_permissions('time_based', group_perms, apps)

class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0051_auto_20210114_1055'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]
