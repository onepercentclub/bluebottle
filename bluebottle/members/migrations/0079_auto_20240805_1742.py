# Generated by Django 3.2.20 on 2024-08-05 15:42

import bluebottle.bb_accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0004_add_permissions_20230130_1255'),
        ('members', '0078_auto_20240805_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='region_manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='offices.officesubregion'),
        ),
    ]
