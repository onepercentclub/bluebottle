# Generated by Django 2.2.24 on 2023-06-29 06:54

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0011_auto_20210913_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationplatformsettings',
            name='match_options',
        ),
    ]
