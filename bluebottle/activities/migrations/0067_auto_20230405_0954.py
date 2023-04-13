# Generated by Django 2.2.24 on 2023-04-05 07:54

from django.db import migrations
from bluebottle.utils.utils import update_group_permissions

def add_group_permissions(apps, schema_editor):
    time_based_permissions = {
        'Staff': {
            'perms': (
                'api_change_dateactivity', 
                'api_change_periodactivity', 
                'api_add_dateactivityslot', 
                'api_delete_dateactivityslot', 
                'api_change_dateactivityslot'
            )
        },
    }

    update_group_permissions('time_based', time_based_permissions, apps)

    funding_permissions = {
        'Staff': {
            'perms': ('api_change_funding', )
        }
    }
    update_group_permissions('funding', funding_permissions, apps)

    collect_permissions = {
        'Staff': {
            'perms': ('api_change_collectactivity', )
        }
    }
    update_group_permissions('collect', collect_permissions, apps)

    deeds_permissions = {
        'Staff': {
            'perms': ('api_change_deed', )
        }
    }
    update_group_permissions('deeds', deeds_permissions, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0066_auto_20221220_1240'),
    ]

    operations = [
            migrations.RunPython(add_group_permissions)
    ]