# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-01-15 07:53
from __future__ import unicode_literals

from django.db import migrations


def pin_latest(apps, schema_editor):
    """
    Pin latest media wallposts
    """
    MediaWallpost = apps.get_model('wallposts', 'MediaWallpost')
    MediaWallpost.objects.order_by('-created','object_id', 'content_type').\
        distinct('object_id', 'content_type').\
        update(pinned=True)


class Migration(migrations.Migration):

    dependencies = [
        ('wallposts', '0017_wallpost_pinned'),
    ]

    operations = [
        migrations.RunPython(pin_latest, migrations.RunPython.noop)
    ]
