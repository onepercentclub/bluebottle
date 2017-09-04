# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-04 09:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_auto_20161228_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stat',
            name='type',
            field=models.CharField(choices=[(b'manual', 'Manual input'), (b'people_involved', 'People involved'), (b'participants', 'Participants'), (b'projects_realized', 'Projects realised'), (b'projects_complete', 'Projects complete'), (b'tasks_realized', 'Tasks realised'), (b'task_members', 'Taskmembers'), (b'donated_total', 'Donated total'), (b'pledged_total', 'Pledged total'), (b'amount_matched', 'Amount matched'), (b'projects_online', 'Projects Online'), (b'votes_cast', 'Votes casts'), (b'time_spent', 'Time spent')], max_length=25),
        ),
    ]
