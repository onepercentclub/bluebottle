# Generated by Django 2.2.24 on 2022-03-01 12:36

import bluebottle.bb_accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0053_auto_20220221_1434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersegment',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
