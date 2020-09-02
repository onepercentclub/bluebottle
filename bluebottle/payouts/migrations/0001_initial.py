# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25

from decimal import Decimal

from django.db import migrations, models
from django.db.models.fields import DecimalField

import django_extensions.db.fields
import django_fsm

import bluebottle.utils.utils


class MoneyField(DecimalField):
    """
    Deprecated MoneyField
    """

    def __init__(self, *args, **kwargs):
        """ Set defaults to 2 decimal places and 12 digits. """
        kwargs['max_digits'] = kwargs.get('max_digits', 12)
        kwargs['decimal_places'] = kwargs.get('decimal_places', 2)
        super(MoneyField, self).__init__(*args, **kwargs)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationPayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_reference', models.CharField(max_length=100)),
                ('completed', models.DateField(blank=True,
                                               help_text='Book date when the bank transaction was confirmed and the payout has been set to completed.',
                                               null=True, verbose_name='Closed')),
                ('planned',
                 models.DateField(help_text='Date on which this batch should be processed.', verbose_name='Planned')),
                ('status', django_fsm.FSMField(
                    choices=[(b'new', 'New'), (b'in_progress', 'In progress'), (b'settled', 'Settled'),
                             (b'retry', 'Retry')], default=b'new', max_length=20, protected=True,
                    verbose_name='status')),
                ('protected', models.BooleanField(default=False,
                                                  help_text='If a payout is protected, the amounts can only be updated via journals.',
                                                  verbose_name='protected')),
                ('created',
                 django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated',
                 django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('submitted', models.DateTimeField(blank=True, null=True, verbose_name='submitted')),
                ('start_date', models.DateField(verbose_name='start date')),
                ('end_date', models.DateField(verbose_name='end date')),
                ('organization_fee_excl',
                 MoneyField(decimal_places=2, max_digits=12, verbose_name='organization fee excluding VAT')),
                ('organization_fee_vat',
                 MoneyField(decimal_places=2, max_digits=12, verbose_name='organization fee VAT')),
                ('organization_fee_incl',
                 MoneyField(decimal_places=2, max_digits=12, verbose_name='organization fee including VAT')),
                ('psp_fee_excl', MoneyField(decimal_places=2, max_digits=12, verbose_name='PSP fee excluding VAT')),
                ('psp_fee_vat', MoneyField(decimal_places=2, max_digits=12, verbose_name='PSP fee VAT')),
                ('psp_fee_incl', MoneyField(decimal_places=2, max_digits=12, verbose_name='PSP fee including VAT')),
                ('other_costs_excl', MoneyField(decimal_places=2, default=Decimal('0.00'),
                                                help_text='Set either this value or inclusive VAT, make sure recalculate afterwards.',
                                                max_digits=12, verbose_name='other costs excluding VAT')),
                ('other_costs_vat',
                 MoneyField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='other costs VAT')),
                ('other_costs_incl', MoneyField(decimal_places=2, default=Decimal('0.00'),
                                                help_text='Set either this value or exclusive VAT, make sure recalculate afterwards.',
                                                max_digits=12, verbose_name='other costs including VAT')),
                ('payable_amount_excl',
                 MoneyField(decimal_places=2, max_digits=12, verbose_name='payable amount excluding VAT')),
                ('payable_amount_vat', MoneyField(decimal_places=2, max_digits=12, verbose_name='payable amount VAT')),
                ('payable_amount_incl',
                 MoneyField(decimal_places=2, max_digits=12, verbose_name='payable amount including VAT')),
            ],
            options={
                'ordering': ['start_date'],
                'abstract': False,
                'get_latest_by': 'end_date',
            },
            bases=(models.Model, bluebottle.utils.utils.FSMTransition),
        ),
        migrations.CreateModel(
            name='ProjectPayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_reference', models.CharField(max_length=100)),
                ('completed', models.DateField(blank=True,
                                               help_text='Book date when the bank transaction was confirmed and the payout has been set to completed.',
                                               null=True, verbose_name='Closed')),
                ('planned',
                 models.DateField(help_text='Date on which this batch should be processed.', verbose_name='Planned')),
                ('status', django_fsm.FSMField(
                    choices=[(b'new', 'New'), (b'in_progress', 'In progress'), (b'settled', 'Settled'),
                             (b'retry', 'Retry')], default=b'new', max_length=20, protected=True,
                    verbose_name='status')),
                ('protected', models.BooleanField(default=False,
                                                  help_text='If a payout is protected, the amounts can only be updated via journals.',
                                                  verbose_name='protected')),
                ('created',
                 django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated',
                 django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('submitted', models.DateTimeField(blank=True, null=True, verbose_name='submitted')),
                ('payout_rule', models.CharField(help_text='The payout rule for this project.', max_length=20,
                                                 verbose_name='Payout rule')),
                ('amount_raised',
                 MoneyField(decimal_places=2, help_text='Amount raised when Payout was created or last recalculated.',
                            max_digits=12, verbose_name='amount raised')),
                ('organization_fee',
                 MoneyField(decimal_places=2, help_text='Fee subtracted from amount raised for the organization.',
                            max_digits=12, verbose_name='organization fee')),
                ('amount_payable',
                 MoneyField(decimal_places=2, help_text='Payable amount; raised amount minus organization fee.',
                            max_digits=12, verbose_name='amount payable')),
                ('sender_account_number', models.CharField(max_length=100)),
                ('receiver_account_number', models.CharField(blank=True, max_length=100)),
                ('receiver_account_iban', models.CharField(blank=True, max_length=100)),
                ('receiver_account_bic', models.CharField(blank=True, max_length=100)),
                ('receiver_account_name', models.CharField(max_length=100)),
                ('receiver_account_city', models.CharField(max_length=100)),
                ('receiver_account_country', models.CharField(max_length=100, null=True)),
                ('description_line1', models.CharField(blank=True, default=b'', max_length=100)),
                ('description_line2', models.CharField(blank=True, default=b'', max_length=100)),
                ('description_line3', models.CharField(blank=True, default=b'', max_length=100)),
                ('description_line4', models.CharField(blank=True, default=b'', max_length=100)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
                'get_latest_by': 'created',
            },
            bases=(models.Model, bluebottle.utils.utils.FSMTransition),
        ),
    ]
