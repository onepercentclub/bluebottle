# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-02 14:41


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('funding', '0035_auto_20191002_1415'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalAccount',
            fields=[
                ('bankaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.BankAccount')),
                ('account_id', models.CharField(max_length=40)),
            ],
            options={
                'verbose_name': 'Stripe external account',
                'verbose_name_plural': 'Stripe exterrnal account',
            },
            bases=('funding.bankaccount',),
        ),
        migrations.CreateModel(
            name='PaymentIntent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intent_id', models.CharField(max_length=30)),
                ('client_secret', models.CharField(max_length=100)),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='funding.Donation')),
            ],
        ),
        migrations.CreateModel(
            name='StripePayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.Payment')),
                ('payment_intent', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='funding_stripe.PaymentIntent')),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.payment',),
        ),
        migrations.CreateModel(
            name='StripePaymentProvider',
            fields=[
                ('paymentprovider_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.PaymentProvider')),
                ('credit_card', models.BooleanField(default=True, verbose_name='Credit card')),
                ('ideal', models.BooleanField(default=False, verbose_name='iDEAL')),
                ('bancontact', models.BooleanField(default=False, verbose_name='Bancontact')),
                ('direct_debit', models.BooleanField(default=False, verbose_name='Direct debit')),
            ],
            options={
                'verbose_name': 'Stripe payment provider',
            },
            bases=('funding.paymentprovider',),
        ),
        migrations.CreateModel(
            name='StripePayoutAccount',
            fields=[
                ('payoutaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.PayoutAccount')),
                ('account_id', models.CharField(max_length=40)),
                ('country', models.CharField(max_length=2)),
                ('document_type', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'verbose_name': 'stripe payout account',
                'verbose_name_plural': 'stripe payout accounts',
            },
            bases=('funding.payoutaccount',),
        ),
        migrations.CreateModel(
            name='StripeSourcePayment',
            fields=[
                ('payment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.Payment')),
                ('source_token', models.CharField(max_length=30)),
                ('charge_token', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.payment',),
        ),
    ]
