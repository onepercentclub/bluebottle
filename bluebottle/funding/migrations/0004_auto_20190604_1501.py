# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-06-04 13:01
from __future__ import unicode_literals

import bluebottle.utils.fields
from decimal import Decimal
from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('funding', '0003_auto_20190604_1459'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='amount',
            field=bluebottle.utils.fields.MoneyField(currency_choices="[('EUR', u'Euro')]", decimal_places=2, default=Decimal('0.0'), max_digits=12),
        ),
        migrations.AlterField(
            model_name='donation',
            name='amount_currency',
            field=djmoney.models.fields.CurrencyField(choices=[(b'EUR', 'Euro')], default='EUR', editable=False, max_length=50),
        ),
        migrations.AlterField(
            model_name='funding',
            name='target',
            field=bluebottle.utils.fields.MoneyField(currency_choices="[('EUR', u'Euro')]", decimal_places=2, default=Decimal('0.0'), max_digits=12),
        ),
        migrations.AlterField(
            model_name='funding',
            name='target_currency',
            field=djmoney.models.fields.CurrencyField(choices=[(b'EUR', 'Euro')], default='EUR', editable=False, max_length=50),
        ),
    ]
