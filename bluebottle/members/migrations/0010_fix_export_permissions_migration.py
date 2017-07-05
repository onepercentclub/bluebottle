# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.db import migrations

logger = logging.getLogger(__name__)

def add_export_permission(apps, schema_editor):
    logger.info("Running add export permission migration")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    try:
        content_type, _ = ContentType.objects.get_or_create(app_label='sites', model='site')
        perm, _ = Permission.objects.get_or_create(codename='export',
                                                   name='Can export platform data',
                                                   content_type=content_type)
        staff, _ = Group.objects.get_or_create(name='Staff')
        staff.permissions.add(perm)
    except Exception as e:
        logger.error(e)

def remove_export_permission(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Permission.objects.filter(codename='export',
                              name='Can export platform data').delete()

class Migration(migrations.Migration):
    """ This migration fixes the migration 0005_auto_20160830_0902 which would gulp exceptions"""
    dependencies = [
        ('members', '0009_merge_20170124_1338'),
    ]

    operations = [
        migrations.RunPython(add_export_permission, remove_export_permission)
    ]
