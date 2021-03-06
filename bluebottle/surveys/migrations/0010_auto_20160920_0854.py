# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-20 06:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_auto_20160720_1140'),
        ('tasks', '0011_auto_20160919_1508'),
        ('surveys', '0009_answer_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.Project'),
        ),
        migrations.AddField(
            model_name='response',
            name='submitted',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='response',
            name='task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.Task'),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
