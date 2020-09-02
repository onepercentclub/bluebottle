# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-03 09:12

import datetime

from django.db import migrations
from django.utils import timezone

from bluebottle.utils.utils import FSMTransition, StatusDefinition


def mark_as_failed(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')

    orders = Order.objects.filter(
        status=StatusDefinition.CREATED,
        created__lte=timezone.now() - datetime.timedelta(days=5)
    )

    orders.update(status=StatusDefinition.FAILED)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_add_group_permissions'),
    ]

    operations = [
        migrations.RunPython(mark_as_failed)
    ]
