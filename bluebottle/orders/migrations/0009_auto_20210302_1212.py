# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 11:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0012_auto_20210302_1212'),
        ('orders', '0008_auto_20190904_0838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='user',
        ),
        migrations.DeleteModel(
            name='Order',
        ),
    ]
