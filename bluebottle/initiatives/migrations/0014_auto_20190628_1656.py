# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-06-28 14:56
from __future__ import unicode_literals

import bluebottle.fsm
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initiatives', '0013_auto_20190527_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='activity_manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_manager_initiatives', to=settings.AUTH_USER_MODEL, verbose_name='activity manager'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='status',
            field=bluebottle.fsm.FSMField(choices=[(b'draft', 'draft'), (b'submitted', 'submitted'), (b'needs_work', 'needs work'), (b'approved', 'approved'), (b'closed', 'closed')], default=b'draft', max_length=20),
        ),
    ]
