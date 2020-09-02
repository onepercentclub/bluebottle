# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-04 09:55


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bb_projects', '0004_add_project_continued_phase'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectphase',
            options={'ordering': ['sequence'], 'permissions': (('api_read_projectphase', 'Can view project phase through API'),)},
        ),
        migrations.AlterModelOptions(
            name='projecttheme',
            options={'ordering': ['name'], 'permissions': (('api_read_projecttheme', 'Can view project theme through API'),), 'verbose_name': 'project theme', 'verbose_name_plural': 'project themes'},
        ),
    ]
