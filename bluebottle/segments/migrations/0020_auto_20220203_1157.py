# Generated by Django 2.2.24 on 2022-02-03 10:57

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('segments', '0019_merge_20220120_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segment',
            name='alternate_names',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200),
                blank=True,
                default=list, size=None),
        ),
        migrations.AddField(
            model_name='segment',
            name='email_domains',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=list,
                help_text='Users with email addresses for this domain are automatically added to this segment',
                size=None, verbose_name='Email domain'),
        ),
    ]
