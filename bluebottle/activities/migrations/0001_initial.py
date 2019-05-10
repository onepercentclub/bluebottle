# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-19 12:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_fsm
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', django_fsm.FSMField(choices=[(b'open', 'open'), (b'full', 'full'), (b'running', 'running'), (b'done', 'done'), (b'closed', 'closed')], default=b'open', max_length=50, protected=True)),
                ('title', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='title')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='slug')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', sorl.thumbnail.fields.ImageField(blank=True, help_text='Main activity picture', max_length=255, upload_to=b'activity_images/', verbose_name='image')),
                ('video_url', models.URLField(blank=True, default=b'', max_length=100, null=True, verbose_name='video')),
            ],
            options={
                'verbose_name': 'Activity',
                'verbose_name_plural': 'Activities',
                'permissions': (('api_read_activity', 'Can view activity through the API'), ('api_read_own_activity', 'Can view own activity through the API')),
            },
        ),
        migrations.CreateModel(
            name='Contribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', django_fsm.FSMField(default=b'new', max_length=50, protected=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributions', to='activities.Activity')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
    ]
