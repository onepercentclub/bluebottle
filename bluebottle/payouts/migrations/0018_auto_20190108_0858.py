# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-01-08 07:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payouts', '0017_delete_in_review_accounts'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stripepayoutaccount',
            name='verification_error',
        ),
    ]
