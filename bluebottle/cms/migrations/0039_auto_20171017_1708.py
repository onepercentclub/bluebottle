# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-17 15:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0038_auto_20171017_1645'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='stattranslation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='stattranslation',
            name='master',
        ),
        migrations.RenameField(
            model_name='stat',
            old_name='temp_title',
            new_name='title',
        ),
        migrations.DeleteModel(
            name='StatTranslation',
        ),
    ]
