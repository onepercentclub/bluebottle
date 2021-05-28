# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-01-05 09:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0019_auto_20201229_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='country',
            field=models.ForeignKey(blank=True, help_text='The (geographic) country this office is located in.', null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.Country'),
        ),
        migrations.AlterField(
            model_name='location',
            name='position',
            field=models.CharField(max_length=42, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='subregion',
            field=models.ForeignKey(blank=True, help_text='The organizational group this office belongs too.', null=True, on_delete=django.db.models.deletion.CASCADE, to='offices.OfficeSubRegion', verbose_name='subregion'),
        ),
    ]
