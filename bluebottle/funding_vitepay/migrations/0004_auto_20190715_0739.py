# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-15 05:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funding_vitepay', '0003_vitepaypaymentprovider_prefix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vitepaypayment',
            name='mobile_number',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
