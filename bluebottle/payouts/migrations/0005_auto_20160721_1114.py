# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-21 09:14
from __future__ import unicode_literals

from django.db import migrations


def add_financial_group(apps, schema_editor):
    ProjectPayout = apps.get_model('payouts', 'ProjectPayout')

    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    new_group, created = Group.objects.get_or_create(name='Financial')

    ct = ContentType.objects.get_for_model(ProjectPayout)

    # Now what - Say I want to add 'Can add project' permission to new_group?
    permission, created = Permission.objects.get_or_create(
        codename='change_projectpayout',
        name='Can change project payout',
        content_type=ct
    )
    new_group.permissions.add(permission)


def remove_financial_group(a, b):
    from django.contrib.auth.models import Group
    Group.objects.get(name='Financial').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payouts', '0004_projectpayout_currency'),
    ]

    operations = [
        migrations.RunPython(add_financial_group, remove_financial_group),
    ]
