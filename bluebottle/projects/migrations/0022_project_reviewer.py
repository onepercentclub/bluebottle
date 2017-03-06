# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-27 15:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0021_merge_20170202_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='reviewer',
            field=models.ForeignKey(help_text='Project Reviewer', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviewer', to=settings.AUTH_USER_MODEL, verbose_name='reviewer'),
        ),
    ]
