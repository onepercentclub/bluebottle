# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-31 14:51
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='main_image',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='Shows at the top of your post.', upload_to=b'blogs', verbose_name='Main image'),
        ),
    ]
