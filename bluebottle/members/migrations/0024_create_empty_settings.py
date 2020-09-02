# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-13 11:15


from django.db import migrations

def create_empty_settings(apps, schema_editor):
    return
    MemberPlatformSettings = apps.get_model('members', 'MemberPlatformSettings')
    MemberPlatformSettings.objects.get_or_create()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0023_memberplatformsettings_require_consent'),
    ]

    operations = [
        migrations.RunPython(create_empty_settings)
    ]
