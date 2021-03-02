# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 13:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bb_projects', '0017_auto_20210302_1417'),
        ('projects', '0095_auto_20210302_1417'),
        ('suggestions', '0005_auto_20210302_1417'),
        ('initiatives', '0030_auto_20210302_1405'),
        ('members', '0041_auto_20210302_1416'),
    ]

    state_operations = [
        migrations.DeleteModel(
            name='ProjectTheme',
        ),
        migrations.DeleteModel(
            name='ProjectThemeTranslation',
        ),

    ]
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations
        ),
        migrations.DeleteModel(
            name='ProjectPhase',
        ),
        migrations.DeleteModel(
            name='ProjectPhaseTranslation',
        ),
    ]
