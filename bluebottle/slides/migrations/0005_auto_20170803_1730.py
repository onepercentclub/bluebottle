# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-03 14:14
from __future__ import unicode_literals

from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_slide', 'change_slide', 'delete_slide',
            )
        }
    }

    update_group_permissions('slides', group_perms)


class Migration(migrations.Migration):

    dependencies = [
        ('slides', '0004_merge_20170124_1338'),
    ]

    operations = [
            migrations.RunPython(add_group_permissions)
    ]
