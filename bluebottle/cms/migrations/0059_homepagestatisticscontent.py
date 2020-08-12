# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-07-15 13:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('fluent_contents', '0001_initial'),
        ('cms', '0058_siteplatformsettingstranslation_start_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomepageStatisticsContent',
            fields=[
                ('contentitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fluent_contents.ContentItem')),
                ('title', models.CharField(blank=True, max_length=50, null=True)),
                ('sub_title', models.CharField(blank=True, max_length=400, null=True)),
            ],
            options={
                'db_table': 'contentitem_cms_homepagestatisticscontent',
                'verbose_name': 'Platform Statistics',
            },
            bases=('fluent_contents.contentitem',),
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
