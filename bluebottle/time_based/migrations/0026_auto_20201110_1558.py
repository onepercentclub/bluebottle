# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-10 14:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0025_auto_20201110_1526'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OnADateActivity',
            new_name='DateActivity',
        ),
        migrations.RenameModel(
            old_name='WithADeadlineActivity',
            new_name='PeriodActivity',
        ),
        migrations.AlterModelOptions(
            name='dateactivity',
            options={'permissions': (('api_read_dateactivity', 'Can view on a date activities through the API'), ('api_add_dateactivity', 'Can add on a date activities through the API'), ('api_change_dateactivity', 'Can change on a date activities through the API'), ('api_delete_dateactivity', 'Can delete on a date activities through the API'), ('api_read_own_dateactivity', 'Can view own on a date activities through the API'), ('api_add_own_dateactivity', 'Can add own on a date activities through the API'), ('api_change_own_dateactivity', 'Can change own on a date activities through the API'), ('api_delete_own_dateactivity', 'Can delete own on a date activities through the API')), 'verbose_name': 'On a date activity', 'verbose_name_plural': 'On A Date Activities'},
        ),
        migrations.AlterModelOptions(
            name='periodactivity',
            options={'permissions': (('api_read_periodactivity', 'Can view during a period activities through the API'), ('api_add_periodactivity', 'Can add during a period activities through the API'), ('api_change_periodactivity', 'Can change during a period activities through the API'), ('api_delete_periodactivity', 'Can delete during a period activities through the API'), ('api_read_own_periodactivity', 'Can view own during a period activities through the API'), ('api_add_own_periodactivity', 'Can add own during a period activities through the API'), ('api_change_own_periodactivity', 'Can change own during a period activities through the API'), ('api_delete_own_periodactivity', 'Can delete own during a period activities through the API')), 'verbose_name': 'During a period activity', 'verbose_name_plural': 'During a period activities'},
        ),
    ]
