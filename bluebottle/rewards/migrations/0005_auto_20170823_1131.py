# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-23 09:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0004_add_group_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reward',
            options={'ordering': ['-project__created', 'amount'], 'permissions': (('api_read_reward', 'Can view reward through the API'), ('api_add_reward', 'Can add reward through the API'), ('api_change_reward', 'Can change reward through the API'), ('api_delete_reward', 'Can delete reward through the API'), ('api_read_own_reward', 'Can view own reward through the API'), ('api_add_own_reward', 'Can add own reward through the API'), ('api_change_own_reward', 'Can change own reward through the API'), ('api_delete_own_reward', 'Can delete own reward through the API')), 'verbose_name': 'Gift', 'verbose_name_plural': 'Gifts'},
        ),
    ]
