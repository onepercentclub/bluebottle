# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('numeric_code', models.CharField(blank=True, help_text='ISO 3166-1 or M.49 numeric code', max_length=3, null=True, unique=True, validators=[django.core.validators.RegexValidator(re.compile(b'[0-9][0-9][0-9]'), 'Enter 3 numeric characters.')], verbose_name='numeric code')),
                ('alpha2_code', models.CharField(blank=True, help_text='ISO 3166-1 alpha-2 code', max_length=2, validators=[django.core.validators.RegexValidator(re.compile(b'[A-Z][A-Z]'), 'Enter 2 capital letters.')], verbose_name='alpha2 code')),
                ('alpha3_code', models.CharField(blank=True, help_text='ISO 3166-1 alpha-3 code', max_length=3, validators=[django.core.validators.RegexValidator(re.compile(b'[A-Z][A-Z][A-Z]'), 'Enter 3 capital letters.')], verbose_name='alpha3 code')),
                ('oda_recipient', models.BooleanField(default=False, help_text="Whether a country is a recipient of Official DevelopmentAssistance from the OECD's Development Assistance Committee.", verbose_name='ODA recipient')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('position', models.CharField(max_length=42, null=True)),
                ('city', models.CharField(blank=True, max_length=255, null=True, verbose_name='city')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', sorl.thumbnail.fields.ImageField(blank=True, help_text='Location picture', max_length=255, null=True, upload_to=b'location_images/', verbose_name='image')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.Country')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('numeric_code', models.CharField(blank=True, help_text='ISO 3166-1 or M.49 numeric code', max_length=3, null=True, unique=True, validators=[django.core.validators.RegexValidator(re.compile(b'[0-9][0-9][0-9]'), 'Enter 3 numeric characters.')], verbose_name='numeric code')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
                'verbose_name': 'region',
                'verbose_name_plural': 'regions',
            },
        ),
        migrations.CreateModel(
            name='SubRegion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('numeric_code', models.CharField(blank=True, help_text='ISO 3166-1 or M.49 numeric code', max_length=3, null=True, unique=True, validators=[django.core.validators.RegexValidator(re.compile(b'[0-9][0-9][0-9]'), 'Enter 3 numeric characters.')], verbose_name='numeric code')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geo.Region', verbose_name='region')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
                'verbose_name': 'sub region',
                'verbose_name_plural': 'sub regions',
            },
        ),
        migrations.AddField(
            model_name='country',
            name='subregion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geo.SubRegion', verbose_name='sub region'),
        ),
    ]
