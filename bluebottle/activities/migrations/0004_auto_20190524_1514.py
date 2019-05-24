# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-24 13:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0003_add_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='initiative',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='initiatives.Initiative'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='slug',
            field=models.SlugField(max_length=100, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
    ]
