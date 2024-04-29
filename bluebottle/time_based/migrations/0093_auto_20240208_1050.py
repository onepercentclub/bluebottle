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
                    "add_deadlineactivity",
                    "change_deadlineactivity",
                    "delete_deadlineactivity",
                    "add_deadlineregistration",
                    "change_deadlineregistration",
                    "delete_deadlineregistration",
                    "add_deadlineparticipant",
                    "change_deadlineparticipant",
                    "delete_deadlineparticipant",
                )
            },
            "Anonymous": {
                "perms": (
                    (
                        "api_read_deadlineactivity",
                        "api_read_deadlineregistration",
                        "api_read_deadlineparticipant",
                    )
                    if not properties.CLOSED_SITE
                    else ()
                )
            },
            "Authenticated": {
                "perms": (
                    "api_add_own_deadlineactivity",
                    "api_add_deadlineregistration",
                    "api_add_deadlineparticipant",
                    "api_read_deadlineactivity",
                    "api_read_deadlineregistration",
                    "api_read_deadlineparticipant",
                    "api_change_own_deadlineactivity",
                    "api_change_own_deadlineregistration",
                    "api_change_own_deadlineparticipant",
                )
            },
        }

    update_group_permissions("time_based", group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0092_auto_20240208_1050"),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop)
    ]
