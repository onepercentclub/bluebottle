# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-31 14:51
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image_logo',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='Category Logo image', max_length=255, null=True, upload_to=b'categories/logos/', verbose_name='logo'),
        ),
    ]
