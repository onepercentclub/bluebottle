# -*- coding: utf-8 -*-
from django.db import migrations, connection

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            'Staff': {
                'perms': (
                    'add_dateregistration',
                    'change_dateregistration',
                    'delete_dateregistration',
                )
            },
            'Anonymous': {
                'perms': (
                    'api_read_dateregistration',
                ) if not properties.CLOSED_SITE else ()
            },
            'Authenticated': {
                'perms': (
                    'api_add_dateregistration',
                    'api_read_dateregistration',
                    'api_change_own_dateregistration',
                )
            }
    }

    update_group_permissions('time_based', group_perms, apps)


class Migration(migrations.Migration):
    dependencies = [
        ('time_based', '0138_auto_20250205_1112'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop)
    ]
