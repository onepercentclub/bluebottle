

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
                    'add_basestatistic', 'change_basestatistic', 'delete_basestatistic',
                    'add_databasestatistic', 'change_databasestatistic', 'delete_databasestatistic',
                    'add_manualstatistic', 'change_manualstatistic', 'delete_manualstatistic',
                    'add_impactstatistic', 'change_impactstatistic', 'delete_impactstatistic',
                )
            },
        }

        update_group_permissions('statistics', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0011_auto_20200722_0810'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]
