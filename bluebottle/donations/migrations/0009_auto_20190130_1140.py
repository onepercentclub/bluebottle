# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-01-30 10:40


import bluebottle.utils.fields
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0008_auto_20170927_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='payout_amount',
            field=bluebottle.utils.fields.MoneyField(currency_choices="[('EUR', u'Euro')]", decimal_places=2, default=Decimal('0.0'), max_digits=12, verbose_name='Payout amount'),
        ),
        migrations.AddField(
            model_name='donation',
            name='payout_amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[(b'EUR', 'Euro')], default='EUR', editable=False, max_length=3),
        ),
    ]
