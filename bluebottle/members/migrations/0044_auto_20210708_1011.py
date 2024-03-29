# Generated by Django 2.2.20 on 2021-07-08 08:11

import bluebottle.utils.fields
import bluebottle.utils.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0043_merge_20210527_1631'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberplatformsettings',
            name='enable_birthdate',
            field=models.BooleanField(default=False, help_text='Show birthdate question in profile form'),
        ),
        migrations.AddField(
            model_name='memberplatformsettings',
            name='enable_gender',
            field=models.BooleanField(default=False, help_text='Show gender question in profile form'),
        ),
        migrations.AlterField(
            model_name='member',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=6, verbose_name='gender'),
        ),
    ]
