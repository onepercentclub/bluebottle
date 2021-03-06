# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-09-09 13:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0004_assignment_is_online'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='applicant',
            options={'permissions': (('api_read_applicant', 'Can view applicant through the API'), ('api_add_applicant', 'Can add applicant through the API'), ('api_change_applicant', 'Can change applicant through the API'), ('api_delete_applicant', 'Can delete applicant through the API'), ('api_read_own_applicant', 'Can view own applicant through the API'), ('api_add_own_applicant', 'Can add own applicant through the API'), ('api_change_own_applicant', 'Can change own applicant through the API'), ('api_delete_own_applicant', 'Can delete own applicant through the API')), 'verbose_name': 'Applicant', 'verbose_name_plural': 'Applicants'},
        ),
    ]
