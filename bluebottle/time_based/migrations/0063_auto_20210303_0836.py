# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-03 07:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0062_auto_20210303_0820'),
    ]

    operations = [
        migrations.RunSQL('alter sequence tasks_skill_id_seq rename to time_based_skill_id_seq;'),
        migrations.RunSQL('alter sequence tasks_skill_translation_id_seq rename to time_based_skill_translation_id_seq;'),
    ]
