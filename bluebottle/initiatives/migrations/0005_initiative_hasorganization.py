# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-16 13:37


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0004_auto_20190416_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='hasOrganization',
            field=models.NullBooleanField(default=None),
        ),
    ]
