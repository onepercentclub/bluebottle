# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-22 11:36
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import Permission, Group

from bluebottle.utils.utils import update_group_permissions


def set_owner_permissions(apps, schema_editor):
    group_perms = {
        'Anonymous': {
            'perms': ('api_read_mediawallpost',)
        },
        'Authenticated': {
            'perms': (
                'api_read_own_mediawallpost', 'api_change_own_mediawallpost', 'api_delete_own_mediawallpost',
                'api_read_own_textwallpost', 'api_change_own_textwallpost', 'api_delete_own_textwallpost',
                'api_read_own_mediawallpostphoto', 'api_change_own_mediawallpostphoto', 'api_delete_own_mediawallpostphoto',
                'api_read_own_reaction', 'api_change_own_reaction', 'api_delete_own_reaction',
                'api_read_own_wallpost', 'api_change_own_wallpost', 'api_delete_own_wallpost',

            )
        }
    }

    update_group_permissions('wallposts', group_perms, apps)

    authenticated = Group.objects.get(name='Authenticated')
    for perm in (
        'api_change_mediawallpost', 'api_delete_mediawallpost', 'api_change_textwallpost',
        'api_delete_textwallpost', 'api_change_mediawallpostphoto', 'api_delete_mediawallpostphoto',
        'api_change_reaction', 'api_delete_reaction',
        'api_change_wallpost', 'api_delete_wallpost'
        ):
        authenticated.permissions.remove(
            Permission.objects.get(
                codename=perm, content_type__app_label='wallposts'
            )
        )


class Migration(migrations.Migration):

    dependencies = [
        ('wallposts', '0013_auto_20170822_1105'),
    ]

    operations = [
        migrations.RunPython(set_owner_permissions)
    ]
