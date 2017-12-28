# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-12-28 12:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mails', '0006_auto_20171212_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='recipients',
            field=models.CharField(blank=True, max_length=600, null=True),
        ),
        migrations.AlterField(
            model_name='mailtranslation',
            name='subject',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Subject'),
        ),
    ]
