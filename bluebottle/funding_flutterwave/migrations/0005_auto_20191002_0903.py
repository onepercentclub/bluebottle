# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-02 07:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funding_flutterwave', '0004_auto_20190918_1633'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='flutterwavebankaccount',
            options={'verbose_name': 'Flutterwave bank account', 'verbose_name_plural': 'Flutterwave bank accounts'},
        ),
        migrations.AlterModelOptions(
            name='flutterwavepaymentprovider',
            options={'verbose_name': 'Flutterwave payment provider'},
        ),
    ]
