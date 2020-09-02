# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-12-11 08:38


from django.db import migrations

from bluebottle.utils.utils import update_group_permissions


def add_group_permissions(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_stripepayoutaccount', 'change_stripepayoutaccount',
                'delete_stripepayoutaccount',
                'add_plainpayoutaccount', 'change_plainpayoutaccount',
                'delete_plainpayoutaccount',
                'add_payoutdocument', 'change_payoutdocument', 'delete_payoutdocument',
            )
        },
    }

    update_group_permissions('payouts', group_perms, apps)


class Migration(migrations.Migration):

    dependencies = [
        ('payouts', '0013_auto_20181207_1340'),
    ]

    operations = [
        migrations.RunPython(add_group_permissions)
    ]
