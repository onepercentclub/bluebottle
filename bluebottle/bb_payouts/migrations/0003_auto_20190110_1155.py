# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-01-10 10:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bb_payouts', '0002_auto_20160523_1525'),
        ('payouts', '0018_auto_20190108_0858')
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationpayoutlog',
            name='payout',
        ),
        migrations.RemoveField(
            model_name='projectpayoutlog',
            name='payout',
        ),
        migrations.DeleteModel(
            name='OrganizationPayoutLog',
        ),
        migrations.DeleteModel(
            name='ProjectPayoutLog',
        ),
    ]
