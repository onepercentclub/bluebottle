# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-11-20 12:06
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0032_auto_20201120_1304'),
        ('funding', '0058_auto_20201118_0954'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoneyContribution',
            fields=[
                ('contribution_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='activities.Contribution')),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('EUR', 'Euro')], default='EUR', editable=False, max_length=50)),
                ('amount', bluebottle.utils.fields.MoneyField(currency_choices=[('EUR', 'Euro')], decimal_places=2, default_currency='EUR', max_digits=12)),
            ],
            options={
                'abstract': False,
            },
            bases=('activities.contribution',),
        ),
        migrations.AlterModelOptions(
            name='donor',
            options={'verbose_name': 'Donor', 'verbose_name_plural': 'Donors'},
        ),
    ]
