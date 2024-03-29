# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-03-29 10:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bb_projects', '0015_auto_20190329_1101'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0008_authenticated-permissions'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Initiative',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_status', models.CharField(choices=[(b'created', 'created'), (b'submitted', 'submitted'), (b'needs_work', 'needs work'), (b'accepted', 'accepted'), (b'cancelled', 'cancelled'), (b'rejected', 'rejected')], default=b'created', max_length=50)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', models.SlugField(max_length=100, verbose_name='slug')),
                ('pitch', models.TextField(blank=True, help_text='Pitch your smart idea in one sentence', verbose_name='pitch')),
                ('story', models.TextField(blank=True, verbose_name='story')),
                ('video_url', models.URLField(blank=True, default=b'', help_text="Do you have a video pitch or a short movie that explains your initiative? Cool! We can't wait to see it! You can paste the link to YouTube or Vimeo video here", max_length=100, null=True, verbose_name='video')),
                ('place', models.CharField(blank=True, help_text='Geographical impact location', max_length=200, null=True)),
                ('categories', models.ManyToManyField(blank=True, to='categories.Category')),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.Image')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='own_initiative', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='review_initiative', to=settings.AUTH_USER_MODEL, verbose_name='reviewer')),
                ('theme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bb_projects.ProjectTheme')),
            ],
            options={
                'verbose_name': 'Initiative',
                'verbose_name_plural': 'Initiatives',
                'permissions': (('api_read_initiative', 'Can view initiative through the API'), ('api_add_initiative', 'Can add initiative through the API'), ('api_change_initiative', 'Can change initiative through the API'), ('api_delete_initiative', 'Can delete initiative through the API'), ('api_read_own_initiative', 'Can view own initiative through the API'), ('api_add_own_initiative', 'Can add own initiative through the API'), ('api_change_own_initiative', 'Can change own initiative through the API'), ('api_change_own_running_initiative', 'Can change own initiative through the API'), ('api_delete_own_initiative', 'Can delete own initiative through the API')),
            },
        ),
    ]
