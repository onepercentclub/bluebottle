# Generated by Django 2.2.24 on 2022-03-14 13:15

from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('funding', '0062_auto_20201222_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='fundingplatformsettings',
            name='anonymous_donations',
            field=models.BooleanField(default=False, verbose_name='Hide names from all donations'),
        ),
    ]
