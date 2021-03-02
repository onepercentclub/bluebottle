# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2021-03-02 11:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fundraisers', '0008_auto_20210302_1218'),
        ('rewards', '0010_auto_20210302_1218'),
        ('suggestions', '0005_auto_20210302_1218'),
        ('projects', '0094_merge_20191107_0943'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customprojectfield',
            name='field',
        ),
        migrations.RemoveField(
            model_name='customprojectfield',
            name='project',
        ),
        migrations.RemoveField(
            model_name='customprojectfieldsettings',
            name='project_settings',
        ),
        migrations.RemoveField(
            model_name='project',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='project',
            name='country',
        ),
        migrations.RemoveField(
            model_name='project',
            name='language',
        ),
        migrations.RemoveField(
            model_name='project',
            name='location',
        ),
        migrations.RemoveField(
            model_name='project',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='project',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='project',
            name='payout_account',
        ),
        migrations.RemoveField(
            model_name='project',
            name='promoter',
        ),
        migrations.RemoveField(
            model_name='project',
            name='reviewer',
        ),
        migrations.RemoveField(
            model_name='project',
            name='status',
        ),
        migrations.RemoveField(
            model_name='project',
            name='task_manager',
        ),
        migrations.RemoveField(
            model_name='project',
            name='theme',
        ),
        migrations.RemoveField(
            model_name='projectaddon',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='projectaddon',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectbudgetline',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectcreatetemplate',
            name='project_settings',
        ),
        migrations.RemoveField(
            model_name='projectlocation',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectphaselog',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectphaselog',
            name='status',
        ),
        migrations.RemoveField(
            model_name='projectsearchfilter',
            name='project_settings',
        ),
        migrations.RemoveField(
            model_name='projectimage',
            name='project',
        ),
        migrations.AlterField(
            model_name='projectimage',
            name='file',
            field=models.FileField(upload_to='project_images/'),
        ),
        migrations.AlterField(
            model_name='projectimage',
            name='name',
            field=models.CharField(blank=True, help_text='Defaults to filename, if left blank', max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='CustomProjectField',
        ),
        migrations.DeleteModel(
            name='CustomProjectFieldSettings',
        ),
        migrations.DeleteModel(
            name='Project',
        ),
        migrations.DeleteModel(
            name='ProjectAddOn',
        ),
        migrations.DeleteModel(
            name='ProjectBudgetLine',
        ),
        migrations.DeleteModel(
            name='ProjectCreateTemplate',
        ),
        migrations.DeleteModel(
            name='ProjectLocation',
        ),
        migrations.DeleteModel(
            name='ProjectPhaseLog',
        ),
        migrations.DeleteModel(
            name='ProjectPlatformSettings',
        ),
        migrations.DeleteModel(
            name='ProjectSearchFilter',
        ),
    ]
