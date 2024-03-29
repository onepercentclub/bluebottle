# Generated by Django 2.2.24 on 2022-08-08 09:13

from django.db import migrations


def open_platforms_required_questions_setting(apps, schema_editor):
    MemberPlatformSettings = apps.get_model('members', 'MemberPlatformSettings')
    MemberPlatformSettings.objects.filter(closed=False).update(required_questions_location='contribution')


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0060_auto_20220804_1016'),
    ]

    operations = [
        migrations.RunPython(
            open_platforms_required_questions_setting,
            migrations.RunPython.noop
        )
    ]
