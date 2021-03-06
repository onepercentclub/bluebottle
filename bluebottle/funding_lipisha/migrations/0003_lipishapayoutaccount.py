# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-30 11:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('funding', '0017_auto_20190728_1319'),
        ('funding_lipisha', '0002_auto_20190717_1637'),
    ]

    operations = [
        migrations.CreateModel(
            name='LipishaPayoutAccount',
            fields=[
                ('payoutaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='funding.PayoutAccount')),
                ('account_number', models.CharField(max_length=40)),
            ],
            options={
                'abstract': False,
            },
            bases=('funding.payoutaccount',),
        ),
    ]
