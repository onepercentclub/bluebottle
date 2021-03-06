# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-24 09:59
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
                    'add_onadateactivity', 'change_onadateactivity', 'delete_onadateactivity',
                    'add_withadeadlineactivity', 'change_withadeadlineactivity', 'delete_withadeadlineactivity',
                    'add_ongoingactivity', 'change_ongoingactivity', 'delete_ongoingactivity',
                )
            },
            'Anonymous': {
                'perms': (
                    'api_read_onadateactivity',
                    'api_read_withadeadlineactivity',
                    'api_read_ongoingactivity',
                ) if not properties.CLOSED_SITE else ()
            },
            'Authenticated': {
                'perms': (
                    'api_read_onadateactivity', 'api_add_own_onadateactivity', 'api_change_own_onadateactivity', 'api_delete_own_onadateactivity',
                    'api_read_withadeadlineactivity', 'api_add_own_withadeadlineactivity', 'api_change_own_withadeadlineactivity', 'api_delete_own_withadeadlineactivity',
                    'api_read_ongoingactivity', 'api_add_own_ongoingactivity', 'api_change_own_ongoingactivity', 'api_delete_own_ongoingactivity',
                )
            }
    }

    update_group_permissions('time_based', group_perms, apps)

class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0002_auto_20201014_1242'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]
