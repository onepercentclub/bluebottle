# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-10-13 15:51


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('payments', '0002_auto_20160718_2345'),
    ]

    operations = [
        migrations.CreateModel(
            name='VitepayPayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='payments.Payment')),
                ('language_code', models.CharField(default=b'en', max_length=10)),
                ('currency_code', models.CharField(default=b'XOF', max_length=10)),
                ('country_code', models.CharField(default=b'ML', max_length=10)),
                ('order_id', models.CharField(max_length=10, null=True)),
                ('description', models.CharField(max_length=500, null=True)),
                ('amount_100', models.IntegerField(null=True)),
                ('buyer_ip_adress', models.CharField(max_length=200, null=True)),
                ('return_url', models.CharField(max_length=500, null=True)),
                ('decline_url', models.CharField(max_length=500, null=True)),
                ('cancel_url', models.CharField(max_length=500, null=True)),
                ('callback_url', models.CharField(max_length=500, null=True)),
                ('email', models.CharField(max_length=500, null=True)),
                ('p_type', models.CharField(default=b'orange_money', max_length=500)),
                ('payment_url', models.CharField(max_length=500, null=True)),
            ],
            options={
                'ordering': ('-created', '-updated'),
                'verbose_name': 'Vitepay Payment',
                'verbose_name_plural': 'Vitepay Payments',
            },
            bases=('payments.payment',),
        ),
    ]
