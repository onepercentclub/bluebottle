# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-09-18 14:07


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('funding', '0029_auto_20190913_1458'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlainBankAccount',
            fields=[
                ('bankaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.BankAccount')),
                ('account_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='bank account number')),
                ('account_holder_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='account holder name')),
                ('account_holder_address', models.CharField(blank=True, max_length=500, null=True, verbose_name='account holder address')),
                ('account_bank_country', models.CharField(blank=True, max_length=100, null=True, verbose_name='bank country')),
                ('account_details', models.CharField(blank=True, max_length=500, null=True, verbose_name='account details')),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.bankaccount',),
        ),
        migrations.RemoveField(
            model_name='bankpayoutaccount',
            name='payoutaccount_ptr',
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='owner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='funding_bank_account', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='reviewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name='BankPayoutAccount',
        ),
    ]
