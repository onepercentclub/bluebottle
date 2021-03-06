
# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-03 14:14
from __future__ import unicode_literals

from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_member', 'change_member', 'delete_member',
            )
        },
        'Anonymous': {
            'perms': ('api_read_member', 'api_read_full_member', )
        },
        'Authenticated': {
            'perms': ('api_read_member', 'api_read_full_member', 'api_add_member', 'api_change_member',)
        }

    }
    update_group_permissions('members', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0014_auto_20170816_1614'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions)
    ]
