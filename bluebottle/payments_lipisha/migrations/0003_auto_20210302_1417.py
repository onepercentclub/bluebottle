# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 13:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments_logger', '0002_auto_20210302_1417'),
        ('payments', '0007_auto_20210302_1417'),
        ('payments_lipisha', '0002_lipishaproject_organisationnumber'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lipishapayment',
            name='payment_ptr',
        ),
        migrations.RemoveField(
            model_name='lipishaproject',
            name='projectaddon_ptr',
        ),
        migrations.DeleteModel(
            name='LipishaPayment',
        ),
        migrations.DeleteModel(
            name='LipishaProject',
        ),
    ]
