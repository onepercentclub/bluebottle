# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-21 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0025_merge_20200819_1654'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organizer',
            options={'verbose_name': 'Activity owner', 'verbose_name_plural': 'Activity owners'},
        ),
        migrations.AlterField(
            model_name='contribution',
            name='contribution_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='review_status',
            field=models.CharField(default='draft', max_length=40),
        ),
        migrations.AlterField(
            model_name='activity',
            name='segments',
            field=models.ManyToManyField(blank=True, related_name='activities', to='segments.Segment', verbose_name='Segment'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='slug',
            field=models.SlugField(default='new', max_length=100, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='video_url',
            field=models.URLField(blank=True, default='', help_text="Do you have a video pitch or a short movie that explains your activity? Cool! We can't wait to see it! You can paste the link to YouTube or Vimeo video here", max_length=100, null=True, verbose_name='video'),
        )
    ]
