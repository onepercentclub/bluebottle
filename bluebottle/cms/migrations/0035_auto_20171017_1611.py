# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-17 14:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0034_auto_20171017_1549'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='steptranslation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='steptranslation',
            name='master',
        ),
        migrations.AddField(
            model_name='step',
            name='header',
            field=models.CharField(default='', max_length=100, verbose_name='Header'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='step',
            name='text',
            field=models.CharField(default='', max_length=400, verbose_name='Text'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='StepTranslation',
        ),
    ]
