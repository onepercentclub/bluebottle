# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fundraisers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fundraiser',
            name='owner',
            field=models.ForeignKey(help_text='Campaigner', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='campaigner'),
        ),
    ]
