# Generated by Django 2.2.24 on 2022-07-20 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0073_auto_20220701_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teamslot',
            name='duration',
            field=models.DurationField(verbose_name='duration'),
        ),
        migrations.AlterField(
            model_name='teamslot',
            name='start',
            field=models.DateTimeField(verbose_name='start date and time'),
        ),
    ]