# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-20 09:40


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fundraisers', '0003_fundraiser_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fundraiser',
            name='owner',
            field=models.ForeignKey(help_text='Project owner', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='initiator'),
        ),
        migrations.AlterField(
            model_name='fundraiser',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project', verbose_name='project'),
        ),
    ]
