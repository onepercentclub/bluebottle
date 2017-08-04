# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-03 14:14
from __future__ import unicode_literals

from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_fundraiser', 'change_fundraiser', 'delete_fundraiser',
            )
        }
    }

    update_group_permissions('fundraisers', group_perms)


class Migration(migrations.Migration):

    dependencies = [
        ('fundraisers', '0006_merge'),
    ]

    operations = [
            migrations.RunPython(add_group_permissions)
    ]
