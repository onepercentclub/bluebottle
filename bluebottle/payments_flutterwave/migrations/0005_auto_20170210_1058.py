# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-10 09:58


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments_flutterwave', '0004_auto_20170207_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flutterwavepayment',
            name='response',
            field=models.TextField(blank=True, help_text='Response from Flutterwave', null=True),
        ),
        migrations.AlterField(
            model_name='flutterwavepayment',
            name='update_response',
            field=models.TextField(blank=True, help_text='Result from Flutterware (status update)', null=True),
        ),
    ]
