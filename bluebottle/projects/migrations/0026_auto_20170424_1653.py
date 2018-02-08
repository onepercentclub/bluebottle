# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-24 14:53
from __future__ import unicode_literals

from django.db import migrations


def correct_needs_approval_status(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    ProjectPayout = apps.get_model('payouts', 'ProjectPayout')

    for project in Project.objects.filter(payout_status='needs_approval'):
        try:
            if project.projectpayout_set.get().status in ('in_progress', 'settled'):
                project.payout_status = None
                project.save()
        except ProjectPayout.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_auto_20170404_1130'),
    ]

    operations = [
        migrations.RunPython(correct_needs_approval_status),
    ]
