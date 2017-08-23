# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-22 09:04
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0029_add_group_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['-created'], 'permissions': (('api_read_task', 'Can view tasks through the API'), ('api_add_task', 'Can add tasks through the API'), ('api_change_task', 'Can change tasks through the API'), ('api_delete_task', 'Can delete tasks through the API'), ('api_read_own_task', 'Can view own tasks through the API'), ('api_add_own_task', 'Can add own tasks through the API'), ('api_change_own_task', 'Can change own tasks through the API'), ('api_delete_own_task', 'Can delete own tasks through the API')), 'verbose_name': 'task', 'verbose_name_plural': 'tasks'},
        ),
        migrations.AlterModelOptions(
            name='taskmember',
            options={'permissions': (('api_read_taskmember', 'Can view taskmembers through the API'), ('api_add_taskmember', 'Can add taskmembers through the API'), ('api_change_taskmember', 'Can change taskmembers through the API'), ('api_delete_taskmember', 'Can delete taskmembers through the API'), ('api_read_own_taskmember', 'Can view own taskmembers through the API'), ('api_add_own_taskmember', 'Can add own taskmembers through the API'), ('api_change_own_taskmember', 'Can change own taskmembers through the API'), ('api_delete_own_taskmember', 'Can delete own taskmembers through the API'), ('api_read_taskmember_resume', 'Can read taskmembers resumes through the API'), ('api_read_own_taskmember_resume', 'Can read own taskmembers resumes through the API')), 'verbose_name': 'task member', 'verbose_name_plural': 'task members'},
        ),
        migrations.AlterField(
            model_name='taskmember',
            name='resume',
            field=bluebottle.utils.fields.PrivateFileField(blank=True, upload_to=b'private/private/private/task-members/resume'),
        ),
        migrations.AlterModelOptions(
            name='skill',
            options={'ordering': ('id',), 'permissions': (('api_read_skill', 'Can view skills through the API'),)},
        ),
    ]
