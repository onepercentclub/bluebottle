# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-01-14 09:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0050_auto_20210112_1515'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dateactivityslot',
            options={'permissions': (('api_read_dateactivityslot', 'Can view on date activity slots through the API'), ('api_add_dateactivityslot', 'Can add on a date activity slots through the API'), ('api_change_dateactivityslot', 'Can change on a date activity slots through the API'), ('api_delete_dateactivityslot', 'Can delete on a date activity slots through the API'), ('api_read_own_dateactivityslot', 'Can view own on a date activity slots through the API'), ('api_add_own_dateactivityslot', 'Can add own on a date activity slots through the API'), ('api_change_own_dateactivityslot', 'Can change own on a date activity slots through the API'), ('api_delete_own_dateactivityslot', 'Can delete own on a date activity slots through the API')), 'verbose_name': 'slot', 'verbose_name_plural': 'slots'},
        ),
        migrations.AlterModelOptions(
            name='periodactivityslot',
            options={'permissions': (('api_read_periodactivityslot', 'Can view over a period activity slots through the API'), ('api_add_periodactivityslot', 'Can add over a period activity slots through the API'), ('api_change_periodactivityslot', 'Can change over a period activity slots through the API'), ('api_delete_periodactivityslot', 'Can delete over a period activity slots through the API'), ('api_read_own_periodactivityslot', 'Can view own over a period activity slots through the API'), ('api_add_own_periodactivityslot', 'Can add own over a period activity slots through the API'), ('api_change_own_periodactivityslot', 'Can change own over a period activity slots through the API'), ('api_delete_own_periodactivityslot', 'Can delete own over a period activity slots through the API')), 'verbose_name': 'slot', 'verbose_name_plural': 'slots'},
        ),
        migrations.AlterField(
            model_name='slotparticipant',
            name='slot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slot_participants', to='time_based.DateActivitySlot'),
        ),
    ]
