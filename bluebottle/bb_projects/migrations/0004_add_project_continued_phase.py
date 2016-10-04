# -*- coding: utf-8 -*-
# Generated by Gannetson on 2016-09-01
from __future__ import unicode_literals

from django.db import migrations


def add_project_continued(apps, schema_editor):
    ProjectPhase = apps.get_model('bb_projects', 'ProjectPhase')
    ProjectPhase.objects.get_or_create(
        id=7,
        viewable=True,
        slug="to-be-continued",
        name="Project - To be continued",
        sequence=7,
        editable=False,
        active=True,
        description=""
    )

class Migration(migrations.Migration):

    dependencies = [
        ('bb_projects', '0003_auto_20160815_1658'),
    ]

    operations = [
        migrations.RunPython(add_project_continued)
    ]
