# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-24 14:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0050_auto_20171024_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoriescontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='linkscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='locationscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='logoscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='projectimagescontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='projectscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='projectsmapcontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='quotescontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='shareresultscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='slidescontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='statscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='stepscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='supportertotalcontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='surveycontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='taskscontent',
            name='sub_title',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
