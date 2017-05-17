# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-03 12:35
from __future__ import unicode_literals

from django.db import migrations, models


def set_deadline_to_apply(apps, schema_editor):
    task = apps.get_model('tasks', 'Task')
    task.objects.filter(deadline_to_apply__isnull=True).update(
        deadline_to_apply=models.F('deadline')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0020_task_deadline_to_apply'),
    ]

    operations = [
        migrations.RunPython(set_deadline_to_apply),
        migrations.AlterField(
            model_name='task',
            name='deadline_to_apply',
            field=models.DateTimeField(default=None, help_text='Deadline to apply', verbose_name='deadline_to_apply'),
            preserve_default=False,
        ),
    ]
