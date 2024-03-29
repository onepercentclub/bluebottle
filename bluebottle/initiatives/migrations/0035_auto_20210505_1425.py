# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-05-05 12:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initiatives', '0034_auto_20210315_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='activity_managers',
            field=models.ManyToManyField(blank=True, help_text='Co-initiators can create and edit activities for this initiative, but cannot edit the initiative itself.', null=True, related_name='activity_managers_initiatives', to=settings.AUTH_USER_MODEL, verbose_name='co-initiators'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='is_open',
            field=models.BooleanField(default=False, help_text='Any authenticated users can start an activity under this initiative.', verbose_name='Is open'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='enable_impact',
            field=models.BooleanField(default=False, help_text='Allow activity managers to indicate the impact they make.'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='enable_multiple_dates',
            field=models.BooleanField(default=False, help_text='Enable date activities to have multiple slots.'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='enable_office_regions',
            field=models.BooleanField(default=False, help_text='Allow admins to add (sub)regions to their offices.'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='enable_open_initiatives',
            field=models.BooleanField(default=False, help_text='Allow admins to open up initiatives for any user to add activities.'),
        ),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='enable_participant_exports',
            field=models.BooleanField(default=False, help_text='Add a link to activities so managers van download a contributor list.'),
        ),
    ]
