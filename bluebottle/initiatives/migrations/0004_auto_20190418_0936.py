# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-18 07:36
from __future__ import unicode_literals

import bluebottle.files.fields
from django.db import migrations, models
import django.db.models.deletion
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0010_initiativeplace'),
        ('initiatives', '0003_auto_20190403_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='utils.Language'),
        ),
        migrations.AddField(
            model_name='initiative',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.Location'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='review_status',
            field=django_fsm.FSMField(choices=[(b'created', 'created'), (b'submitted', 'submitted'), (b'needs_work', 'needs work'), (b'approved', 'approved'), (b'cancelled', 'cancelled'), (b'rejected', 'rejected')], default=b'created', max_length=50, protected=True),
        ),
        migrations.AddField(
            model_name='initiative',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='initiative',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
