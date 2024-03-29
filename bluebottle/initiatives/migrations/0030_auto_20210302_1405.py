# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 13:05
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import parler.models


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0029_auto_20210216_0916'),
        ('bb_projects', '0016_auto_20210302_1338'),
    ]
    state_operations = [
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='slug')),
                ('disabled', models.BooleanField(default=False, verbose_name='disabled')),
            ],
            options={
                'verbose_name': 'Theme',
                'verbose_name_plural': 'Themes',
                'permissions': (('api_read_theme', 'Can view theme through API'),),
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),

        migrations.CreateModel(
            name='ThemeTranslation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('master', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='initiatives.Theme')),
            ],
            options={
                'verbose_name': 'Theme Translation',
                'db_tablespace': '',
                'managed': True,
                'default_permissions': (),
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations),
        migrations.AlterField(
            model_name='initiative',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='initiatives.Theme', verbose_name='theme'),
        ),
    ]