# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 11:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_auto_20210302_1209'),
        ('payments_logger', '0002_auto_20210302_1209'),
        ('payments_interswitch', '0003_interswitchpaymentstatusupdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interswitchpayment',
            name='payment_ptr',
        ),
        migrations.RemoveField(
            model_name='interswitchpaymentstatusupdate',
            name='payment',
        ),
        migrations.DeleteModel(
            name='InterswitchPayment',
        ),
        migrations.DeleteModel(
            name='InterswitchPaymentStatusUpdate',
        ),
    ]
