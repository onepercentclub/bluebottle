# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-29 06:49


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0027_auto_20160929_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='left_label',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='right_label',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='subquestion',
            name='display_title',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
