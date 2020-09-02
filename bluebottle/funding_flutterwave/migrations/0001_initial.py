# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-03 11:30


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('funding', '0011_auto_20190617_1251'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlutterwavePayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.Payment')),
                ('tx_ref', models.CharField(max_length=30)),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.payment',),
        ),
        migrations.CreateModel(
            name='FlutterwavePaymentProvider',
            fields=[
                ('paymentprovider_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.PaymentProvider')),
                ('pub_key', models.CharField(max_length=100)),
                ('sec_key', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.paymentprovider',),
        ),
    ]
