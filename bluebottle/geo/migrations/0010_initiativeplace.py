# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-04-03 14:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0009_merge_20190121_1425'),
    ]

    operations = [
        migrations.CreateModel(
            name='InitiativePlace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_number', models.CharField(blank=True, max_length=255, null=True, verbose_name='Street Number')),
                ('street', models.CharField(blank=True, max_length=255, null=True, verbose_name='Street')),
                ('postal_code', models.CharField(blank=True, max_length=255, null=True, verbose_name='Postal Code')),
                ('locality', models.CharField(blank=True, max_length=255, null=True, verbose_name='Locality')),
                ('province', models.CharField(blank=True, max_length=255, null=True, verbose_name='Province')),
                ('formatted_address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Address')),
                ('position', models.CharField(max_length=42)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geo.Country')),
            ],
        ),
    ]
