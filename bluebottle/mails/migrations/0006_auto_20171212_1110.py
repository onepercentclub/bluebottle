# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-12-12 10:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mails', '0005_auto_20171212_0930'),
    ]

    operations = [
        migrations.AddField(
            model_name='mail',
            name='action_link',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Action link'),
        ),
        migrations.AddField(
            model_name='mailtranslation',
            name='action_title',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Action title'),
        ),
    ]
