# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-16 14:53
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0068_auto_20180306_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='project',
            name='longitude',
        ),
        migrations.AlterField(
            model_name='projectcreatetemplate',
            name='default_amount_asked',
            field=bluebottle.utils.fields.MoneyField(blank=True, currency_choices="[('EUR', u'Euro')]", decimal_places=2, default=None, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='projectlocation',
            name='latitude',
            field=models.DecimalField(decimal_places=18, max_digits=21, null=True, verbose_name='latitude'),
        ),
        migrations.AlterField(
            model_name='projectlocation',
            name='longitude',
            field=models.DecimalField(decimal_places=18, max_digits=21, null=True, verbose_name='longitude'),
        ),
    ]
