from django.db import connection, migrations

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            'Staff': {
                'perms': (
                    'add_organizationmember',
                    'change_organizationmember',
                    'delete_organizationmember',
                    'view_organizationmember',
                )
            },
        }
        update_group_permissions('organizations', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0030_convert_partner_organization_to_members'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop),
    ]
