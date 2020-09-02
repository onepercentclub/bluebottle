

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
                    'add_impacttype', 'change_impacttype', 'delete_impacttype',
                    'add_impactgoal', 'change_impactgoal', 'delete_impactgoal',
                )
            },
        }

        update_group_permissions('impact', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0010_impacttypetranslation_unit'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]
