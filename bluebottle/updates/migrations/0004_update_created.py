# Generated by Django 3.2.19 on 2023-07-21 09:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0003_update_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='created'),
        ),
    ]
