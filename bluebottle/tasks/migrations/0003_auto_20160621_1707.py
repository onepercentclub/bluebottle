# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-21 15:07


from django.db import migrations

from django.db import connection
from bluebottle.clients.utils import LocalTenant

def update_time_spent(apps, schema_editor):
    TaskMember = apps.get_model('tasks', "TaskMember")
    with LocalTenant(connection.tenant):
            for tm in TaskMember.objects.filter(status='realized'):
                if tm.task and tm.task.time_needed:
                    tm.time_spent = tm.task.time_needed
                    tm.save()


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20160614_1354'),
    ]

    operations = [
		migrations.RunPython(update_time_spent),
    ]
