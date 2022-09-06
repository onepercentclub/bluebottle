# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 14:47
from __future__ import unicode_literals

from bluebottle.clients.models import Client

from bluebottle.clients.utils import LocalTenant

from bluebottle.clients import properties

from bluebottle.utils.utils import update_group_permissions
from django.db import migrations, connection


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            'Anonymous': {
                'perms': (
                    'api_read_slotparticipant',
                ) if not properties.CLOSED_SITE else ()
            },
            'Authenticated': {
                'perms': (
                    'api_read_slotparticipant',
                )
            }
    }
    update_group_permissions('time_based', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0060_auto_20210302_0905'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions)
    ]
