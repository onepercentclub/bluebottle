# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-06 12:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0004_auto_20160929_0817'),
        ('payments', '0005_auto_20170919_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethodCurrencySettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(choices=[(b'EUR', 'Euro')], default='EUR', max_length=3)),
                ('min_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('max_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentMethodSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile', models.CharField(help_text='The payment method short name, e.g. creditcard', max_length=100)),
                ('name', models.CharField(help_text='The payment method long name, e.g. Credit Card', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentPlatformSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'payment platform settings',
                'verbose_name_plural': 'payment platform settings',
            },
        ),
        migrations.CreateModel(
            name='PaymentProviderSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('settings', django_extensions.db.fields.json.JSONField(default=dict)),
            ],
        ),
        migrations.AddField(
            model_name='paymentmethodsettings',
            name='provider',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.PaymentProviderSettings'),
        ),
        migrations.AddField(
            model_name='paymentmethodsettings',
            name='restricted_countries',
            field=models.ManyToManyField(blank=True, null=True, to='geo.Country'),
        ),
        migrations.AddField(
            model_name='paymentmethodsettings',
            name='settings',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='payments.PaymentPlatformSettings'),
        ),
        migrations.AddField(
            model_name='paymentmethodcurrencysettings',
            name='payment_method',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.PaymentMethodSettings'),
        ),
    ]
