# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-09 09:24


from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('contentplugins', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='pictureitem',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
