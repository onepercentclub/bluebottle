# Generated by Django 3.2.20 on 2024-01-15 10:06

import bluebottle.bb_accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0033_auto_20231211_1541'),
        ('members', '0075_auto_20230714_1120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='about_me',
            field=models.TextField(blank=True, verbose_name='about me'),
        ),
    ]
