# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-08 10:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0021_auto_20170503_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='accepting',
            field=models.CharField(choices=[(b'manual', 'Manual'), (b'automatic', 'Automatic')], default=b'manual', max_length=20, verbose_name='accepting'),
        ),
    ]
