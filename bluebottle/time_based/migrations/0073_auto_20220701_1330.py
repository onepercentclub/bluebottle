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
                    'add_teamslot', 'change_teamslot', 'delete_teamslot',
                )
            },
            'Anonymous': {
                'perms': (
                    'api_read_teamslot',
                ) if not properties.CLOSED_SITE else ()
            },
            'Authenticated': {
                'perms': (
                    'api_read_teamslot', 'api_add_own_teamslot',
                    'api_change_own_teamslot', 'api_delete_own_teamslot',
                )
            }
    }

    update_group_permissions('time_based', group_perms, apps)

class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0072_teamslot_duration'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]
