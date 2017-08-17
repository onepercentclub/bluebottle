# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-03 14:14
from __future__ import unicode_literals

from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_project', 'change_project', 'delete_project',
                'add_projectdocument', 'change_projectdocument', 'delete_projectdocument',
                'add_projectbudgetline', 'change_projectbudgetline', 'delete_projectbudgetline',
            )
        },
        'Anonymous': {
            'perms': ('api_read_project',)
        },
        'Authenticated': {
            'perms': ('api_read_project', 'api_add_project', 'api_change_project',
                      'api_read_projectdocument', 'api_add_projectdocument', 'api_change_projectdocument',
                      'api_read_projectbudgetline', 'api_add_projectbudgetline',
                      'api_change_projectbudgetline', 'api_delete_projectbudgetline',)
        }
    }

    update_group_permissions('projects', group_perms)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0031_add_api_permissions'),
    ]

    operations = [
            migrations.RunPython(add_group_permissions)
    ]
