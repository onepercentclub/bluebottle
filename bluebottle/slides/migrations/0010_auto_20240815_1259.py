# Generated by Django 3.2.20 on 2024-08-15 10:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0004_add_permissions_20230130_1255'),
        ('slides', '0009_auto_20230719_1330'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='sub_region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offices.officesubregion', verbose_name='Office group'),
        ),
    ]
