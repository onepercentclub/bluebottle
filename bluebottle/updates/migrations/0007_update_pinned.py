# Generated by Django 3.2.19 on 2023-07-25 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0006_auto_20230725_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='pinned',
            field=models.BooleanField(default=True, verbose_name='Pinned'),
        ),
    ]