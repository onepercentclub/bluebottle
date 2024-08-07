from django.db import migrations, connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.utils.utils import update_group_permissions

permissions = [
    'add_periodicslot',
    'change_periodicslot',
    'delete_periodicslot',

    'add_scheduleslot',
    'change_scheduleslot',
    'delete_scheduleslot',

    'add_teamscheduleslot',
    'change_teamscheduleslot',
    'delete_teamscheduleslot',

    'add_teamscheduleregistration',
    'change_teamscheduleregistration',
    'delete_teamscheduleregistration',

    'add_teamscheduleparticipant',
    'change_teamscheduleparticipant',
    'delete_teamscheduleparticipant',
]


def add_group_permissions(apps, schema_editor):
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        group_perms = {
            "Staff": {"perms": permissions},
        }

    update_group_permissions("time_based", group_perms, apps)



class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0129_auto_20240801_1320'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions, migrations.RunPython.noop),
    ]
