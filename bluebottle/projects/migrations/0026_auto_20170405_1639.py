# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-05 14:39
from __future__ import unicode_literals

from django.db import migrations


def add_permission(a, b):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from bluebottle.projects.models import Project

    group = Group.objects.get(name='Financial')
    ct = ContentType.objects.get_for_model(Project)

    (permission, created) = Permission.objects.get_or_create(
        codename='approve_payout',
        name='Can approve payouts for projects',
        content_type=ct
    )
    group.permissions.add(permission)



class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_auto_20170404_1130'),
    ]

    operations = [
        migrations.RunPython(add_permission),
    ]
