# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-19 13:08


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='link',
            field=models.URLField(default=''),
            preserve_default=False,
        ),
    ]
