# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-24 16:12


import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0007_auto_20170803_1730'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='logo',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='Partner Organization Logo', max_length=255, null=True, upload_to=b'partner_organization_logos/', verbose_name='image'),
        ),
    ]
