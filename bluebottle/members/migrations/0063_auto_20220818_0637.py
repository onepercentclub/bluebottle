# Generated by Django 2.2.24 on 2022-08-18 04:37

import bluebottle.bb_accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0062_auto_20220815_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberplatformsettings',
            name='do_good_hours',
            field=models.IntegerField(
                blank=True,
                help_text='The amount of hours users can spend each year. '
                          'Leave empty if no restrictions apply.',
                null=True
            ),
        ),
    ]
