# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-13 07:09
from __future__ import unicode_literals

import bluebottle.files.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0007_merge_20190501_0922'),
    ]

    operations = [
        migrations.RenameField(
            model_name='initiative',
            old_name='review_status',
            new_name='status',
        ),
        migrations.AlterField(
            model_name='initiative',
            name='image',
            field=bluebottle.files.fields.ImageField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='files.Image'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='promoter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='promoter'),
        ),
    ]
