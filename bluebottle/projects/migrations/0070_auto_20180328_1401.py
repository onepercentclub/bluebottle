# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-28 12:01


from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'change_projectlocation',
            )
        },
    }

    update_group_permissions('projects', group_perms, apps)



class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0069_auto_20180316_1553'),
    ]

    operations = [
            migrations.RunPython(add_group_permissions)
    ]
