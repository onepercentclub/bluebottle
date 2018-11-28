# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-11-28 08:10
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_auto_20170919_1621'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderpayment',
            options={'permissions': (('refund_orderpayment', 'Can refund order payments'),), 'verbose_name': 'order payment', 'verbose_name_plural': 'order payments'},
        ),
        migrations.AlterModelOptions(
            name='payment',
            options={'ordering': ('-created', '-updated'), 'verbose_name': 'payment', 'verbose_name_plural': 'payments'},
        ),
        migrations.AddField(
            model_name='orderpayment',
            name='new_integration_data',
            field=django.contrib.postgres.fields.JSONField(null=True, blank=True, default="{}", verbose_name='Integration data'),
        ),
        migrations.AlterField(
            model_name='orderpayment',
            name='status',
            field=django_fsm.FSMField(choices=[(b'created', 'Created'), (b'started', 'Started'), (b'cancelled', 'Cancelled'), (b'pledged', 'Pledged'), (b'authorized', 'Authorized'), (b'settled', 'Settled'), (b'charged_back', 'Charged_back'), (b'refund_requested', 'Refund requested'), (b'refunded', 'Refunded'), (b'failed', 'Failed'), (b'unknown', 'Unknown')], default=b'created', max_length=50, protected=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=django_fsm.FSMField(choices=[(b'created', 'Created'), (b'started', 'Started'), (b'cancelled', 'Cancelled'), (b'pledged', 'Pledged'), (b'authorized', 'Authorized'), (b'settled', 'Settled'), (b'charged_back', 'Charged_back'), (b'refund_requested', 'Refund requested'), (b'refunded', 'Refunded'), (b'failed', 'Failed'), (b'unknown', 'Unknown')], default=b'started', max_length=50),
        ),
    ]
