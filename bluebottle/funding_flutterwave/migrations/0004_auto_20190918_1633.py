# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-09-18 14:33


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('funding', '0031_plainpayoutaccount'),
        ('funding_flutterwave', '0003_flutterwavepayoutaccount'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlutterwaveBankAccount',
            fields=[
                ('bankaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.BankAccount')),
                ('account', models.CharField(blank=True, max_length=100, null=True, verbose_name='flutterwave account')),
                ('account_holder_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='account holder name')),
                ('bank_country_code', models.CharField(blank=True, default=b'NG', max_length=2, null=True, verbose_name='bank country code')),
                ('bank_code', models.CharField(blank=True, max_length=100, null=True, verbose_name='bank code')),
                ('account_number', models.CharField(blank=True, max_length=255, null=True, verbose_name='account number')),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.bankaccount',),
        ),
        migrations.RemoveField(
            model_name='flutterwavepayoutaccount',
            name='payoutaccount_ptr',
        ),
        migrations.DeleteModel(
            name='FlutterwavePayoutAccount',
        ),
    ]
