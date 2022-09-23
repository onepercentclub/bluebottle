# Generated by Django 2.2.24 on 2022-09-23 12:20

import bluebottle.bb_accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0067_auto_20220923_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberplatformsettings',
            name='fiscal_month_offset',
            field=models.IntegerField(blank=True, default=0, help_text='Set the number of months your fiscal year will be offset by. This will also take into account how the impact metrics are shown on the homepage. e.g. If the year starts from September (so earlier) then this value should be -4.', null=True, verbose_name='Fiscal year offset'),
        ),
    ]
