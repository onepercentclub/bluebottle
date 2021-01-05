# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-10-26 13:35
from __future__ import unicode_literals

import bluebottle.activities.models
import bluebottle.fsm.triggers
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('activities', '0026_auto_20201021_1420'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContributionValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=40)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('contribution', models.ForeignKey(on_delete=bluebottle.activities.models.NON_POLYMORPHIC_CASCADE, related_name='contributions', to='activities.Contribution')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_activities.contributionvalue_set+', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-created',),
            },
            bases=(bluebottle.fsm.triggers.TriggerMixin, models.Model),
        ),
    ]
