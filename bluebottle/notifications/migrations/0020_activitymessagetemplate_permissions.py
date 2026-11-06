from django.db import migrations, connection

from bluebottle.utils.utils import update_group_permissions

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            "Staff": {
                "perms": (
                    "add_activitymessagetemplate",
                    "change_activitymessagetemplate",
                    "delete_activitymessagetemplate",
                )
            },
            "Authenticated": {
                "perms": (
                    "api_read_own_activitymessagetemplate",
                    "api_add_own_activitymessagetemplate",
                    "api_change_own_activitymessagetemplate",
                    "api_delete_own_activitymessagetemplate",
                )
            },
        }

    update_group_permissions("notifications", group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0019_activitymessagetemplate"),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop)
    ]
