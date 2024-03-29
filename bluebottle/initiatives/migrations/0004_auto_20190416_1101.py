# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-16 09:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0012_auto_20190416_1101'),
        ('initiatives', '0003_auto_20190403_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.Organization'),
        ),
        migrations.AddField(
            model_name='initiative',
            name='organization_contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.OrganizationContact'),
        ),
        migrations.AddField(
            model_name='initiative',
            name='promoter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='review_status',
            field=models.CharField(choices=[(b'created', 'created'), (b'submitted', 'submitted'), (b'needs_work', 'needs work'), (b'approved', 'approved'), (b'cancelled', 'cancelled'), (b'rejected', 'rejected')], default=b'created', max_length=50),
        ),
    ]
