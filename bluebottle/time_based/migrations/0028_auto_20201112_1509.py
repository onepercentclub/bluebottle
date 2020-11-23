# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-12 14:09
from __future__ import unicode_literals

from django.db import migrations, models

from bluebottle.utils.operations import AlterBaseOperation
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0027_auto_20201110_1613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodapplication',
            name='contribution_ptr',
            field=models.OneToOneField(
                auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                primary_key=True, serialize=False, to='activities.Contributor')
        ),
        migrations.AlterField(
            model_name='onadateapplication',
            name='contribution_ptr',
            field=models.OneToOneField(
                auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                primary_key=True, serialize=False, to='activities.Contributor')
        )
    ]
