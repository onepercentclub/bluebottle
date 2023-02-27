# Generated by Django 2.2.24 on 2023-01-30 11:55
from bluebottle.utils.utils import update_group_permissions
from django.db import migrations


def add_group_permissions(apps, schema_editor):
    office_perms = {
        'Staff': {
            'perms': (
                'add_officeregion',
                'change_officeregion',
                'delete_officeregion',
                'add_officesubregion',
                'change_officesubregion',
                'delete_officesubregion',
            )
        },
    }

    update_group_permissions('offices', office_perms, apps)

    geo_perms = {
        'Staff': {
            'perms': (
                'add_location',
                'change_location',
                'delete_location',
                'add_place',
                'change_place',
                'delete_place',
            )
        },
    }

    update_group_permissions('geo', geo_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0003_auto_20210414_1507'),
    ]

    operations = [
        migrations.RunPython(
            add_group_permissions,
            migrations.RunPython.noop
        )
    ]