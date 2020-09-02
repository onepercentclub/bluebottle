# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-29 06:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_project_celebrate_results'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='celebrate_results',
            field=models.BooleanField(default=True, help_text='Show celebration when project is complete', verbose_name='Celebrate Results'),
        ),
    ]
