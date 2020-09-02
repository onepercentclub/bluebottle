# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-08-04 05:50


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0038_auto_20200801_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberplatformsettings',
            name='create_segments',
            field=models.BooleanField(default=False, help_text='Create new segments when a user logs in. Leave unchecked if only priorly specified ones should be used.'),
        ),
        migrations.AlterField(
            model_name='memberplatformsettings',
            name='enable_segments',
            field=models.BooleanField(default=False, help_text='Enable segments for users e.g. department or job title.'),
        ),
    ]
