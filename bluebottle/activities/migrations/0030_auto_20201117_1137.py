# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-17 10:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0029_auto_20201112_1519'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contributor',
            options={'ordering': ('-created',), 'verbose_name': 'Contributor', 'verbose_name_plural': 'Contributors'},
        ),
        migrations.AlterField(
            model_name='activity',
            name='transition_date',
            field=models.DateTimeField(blank=True, help_text='Date the activity took place.', null=True, verbose_name='activity date'),
        ),
    ]
