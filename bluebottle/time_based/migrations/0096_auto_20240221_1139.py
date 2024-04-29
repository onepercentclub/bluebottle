# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import unicode_literals

from django.db import migrations, connection

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            "Staff": {
                "perms": (
                    "add_periodicactivity",
                    "change_periodicactivity",
                    "delete_periodicactivity",
                    "add_periodicregistration",
                    "change_periodicregistration",
                    "delete_periodicregistration",
                    "add_periodicparticipant",
                    "change_periodicparticipant",
                    "delete_periodicparticipant",
                )
            },
            "Anonymous": {
                "perms": (
                    (
                        "api_read_periodicactivity",
                        "api_read_periodicregistration",
                        "api_read_periodicparticipant",
                    )
                    if not properties.CLOSED_SITE
                    else ()
                )
            },
            "Authenticated": {
                "perms": (
                    "api_add_own_periodicactivity",
                    "api_add_periodicregistration",
                    "api_add_periodicparticipant",
                    "api_read_periodicactivity",
                    "api_read_periodicregistration",
                    "api_read_periodicparticipant",
                    "api_change_own_periodicactivity",
                    "api_change_own_periodicregistration",
                    "api_change_own_periodicparticipant",
                )
            },
        }

    update_group_permissions("time_based", group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0095_auto_20240221_1139"),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop)
    ]
