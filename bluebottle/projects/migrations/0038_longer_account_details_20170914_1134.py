# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-14 09:34


import bluebottle.utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0037_longer_place_20170914_1129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='account_details',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='account details'),
        ),
    ]
