# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-10 11:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0041_remove_untranslated_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='skill',
            options={'ordering': ['translations__name'], 'permissions': (('api_read_skill', 'Can view skills through the API'),), 'verbose_name': 'Skill', 'verbose_name_plural': 'Skills'},
        ),
        migrations.AlterModelOptions(
            name='skilltranslation',
            options={'default_permissions': (), 'managed': True, 'verbose_name': 'Skill Translation'},
        ),
        migrations.AlterModelOptions(
            name='taskmemberstatuslog',
            options={'verbose_name': 'task member status log', 'verbose_name_plural': 'task member status logs'},
        ),
        migrations.AlterModelOptions(
            name='taskstatuslog',
            options={'verbose_name': 'task status log', 'verbose_name_plural': 'task status logs'},
        ),
        migrations.AlterField(
            model_name='skill',
            name='expertise',
            field=models.BooleanField(default=True, help_text='Is this skill expertise based, or could anyone do it?', verbose_name='expertise based'),
        ),
        migrations.AlterField(
            model_name='task',
            name='deadline_to_apply',
            field=models.DateTimeField(help_text='Deadline to apply', verbose_name='deadline to apply'),
        ),
        migrations.AlterField(
            model_name='task',
            name='needs_motivation',
            field=models.BooleanField(default=False, help_text='Indicates if a task candidate needs to submit a motivation', verbose_name='needs motivation'),
        ),
        migrations.AlterField(
            model_name='task',
            name='skill',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.Skill', verbose_name='expertise'),
        ),
        migrations.AlterField(
            model_name='task',
            name='time_needed',
            field=models.FloatField(help_text='Estimated number of hours needed to perform this task.', verbose_name='time needed'),
        ),
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(choices=[(b'ongoing', 'Ongoing (with deadline)'), (b'event', 'Event (on set date)')], default=b'ongoing', max_length=20, verbose_name='ongoing / event'),
        ),
        migrations.AlterField(
            model_name='taskfile',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterUniqueTogether(
            name='skilltranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
