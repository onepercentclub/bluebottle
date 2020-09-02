# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-23 12:22


import bluebottle.utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0026_auto_20170424_1653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectdocument',
            name='file',
            field=bluebottle.utils.fields.PrivateFileField(
                max_length=110,
                upload_to=b'private/private/private/projects/documents'
            ),
        ),
    ]
