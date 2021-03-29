# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-28 19:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hooks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebHookLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=50)),
                ('instance_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_logs', to='contenttypes.ContentType')),
            ],
        ),
    ]
