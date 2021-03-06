# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-28 12:14
from __future__ import unicode_literals

import bluebottle.utils.fields
from django.db import migrations, models
import multiselectfield


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0077_auto_20180518_1050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectplatformsettings',
            name='share_options',
            field=multiselectfield.MultiSelectField(blank=True, choices=[(b'twitter', 'Twitter'), (b'facebook', 'Facebook'), (b'facebookAtWork', 'Facebook at Work'), (b'linkedin', 'LinkedIn'), (b'whatsapp', 'Whatsapp'), (b'email', 'Email')], max_length=100),
        ),
    ]
