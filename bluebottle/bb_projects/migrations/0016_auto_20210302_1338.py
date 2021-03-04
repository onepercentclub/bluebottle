# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 12:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bb_projects', '0015_auto_20190329_1101'),
    ]

    database_operations = [
        migrations.AlterModelTable('ProjectTheme', 'initiatives_theme'),
        migrations.AlterModelTable('ProjectThemeTranslation', 'initiatives_theme_translation')
    ]

    operations = [
      migrations.SeparateDatabaseAndState(
        database_operations=database_operations
      )
    ]
