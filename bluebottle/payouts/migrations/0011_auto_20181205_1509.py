# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-12-05 14:09
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payouts', '0010_auto_20181203_1145'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payoutaccount',
            options={'permissions': (('api_read_payoutdocument', 'Can view payout documents through the API'), ('api_add_payoutdocument', 'Can add payout documents through the API'), ('api_change_payoutdocument', 'Can change payout documents through the API'), ('api_delete_payoutdocument', 'Can delete payout documents through the API'), ('api_read_own_payoutdocument', 'Can view payout own documents through the API'), ('api_add_own_payoutdocument', 'Can add own payout documents through the API'), ('api_change_own_payoutdocument', 'Can change own payout documents through the API'), ('api_delete_own_payoutdocument', 'Can delete own payout documents through the API'))},
        ),
        migrations.AlterField(
            model_name='payoutdocument',
            name='file',
            field=bluebottle.utils.fields.PrivateFileField(max_length=110, upload_to=b'private/payouts/documents'),
        ),
    ]
