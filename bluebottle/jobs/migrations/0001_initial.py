# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-13 10:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('activities', '0001_initial')
    ]

    operations = [
        migrations.CreateModel(
            name='Applicant',
            fields=[
                ('contribution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='activities.Contribution')),
                ('motivation', models.TextField()),
                ('time_spent', models.FloatField(verbose_name='time spent')),
            ],
            bases=('activities.contribution',),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('activity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='activities.Activity')),
                ('registration_deadline', models.DateTimeField(verbose_name='registration deadline')),
                ('end', models.DateField(verbose_name='end')),
                ('capacity', models.PositiveIntegerField()),
                ('location', models.CharField(blank=True, help_text='Location the job takes place', max_length=200, null=True)),
                ('expertise', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.Skill', verbose_name='expertise')),
            ],
            options={
                'verbose_name': 'Job',
                'verbose_name_plural': 'Jobs',
                'permissions': (('api_read_job', 'Can view job through the API'), ('api_add_job', 'Can add job through the API'), ('api_change_job', 'Can change job through the API'), ('api_delete_job', 'Can delete job through the API'), ('api_read_own_job', 'Can view own job through the API'), ('api_add_own_job', 'Can add own job through the API'), ('api_change_own_job', 'Can change own job through the API'), ('api_delete_own_job', 'Can delete own job through the API')),
            },
            bases=('activities.activity',),
        ),
    ]
