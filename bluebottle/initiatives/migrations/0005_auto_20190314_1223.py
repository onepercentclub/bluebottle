# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-03-14 11:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0004_auto_20190312_1540'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='themetranslation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='themetranslation',
            name='master',
        ),
        migrations.AlterField(
            model_name='initiative',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bb_projects.ProjectTheme'),
        ),
        migrations.DeleteModel(
            name='Theme',
        ),
        migrations.DeleteModel(
            name='ThemeTranslation',
        ),
    ]
