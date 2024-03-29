# Generated by Django 2.2.24 on 2022-03-01 12:36

from django.db import migrations

def unset_verified(apps, schema_editor):
    UserSegment = apps.get_model('members', 'UserSegment')

    UserSegment.objects.all().update(verified=False)


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0054_auto_20220301_1336'),
    ]

    operations = [
        migrations.RunPython(unset_verified, migrations.RunPython.noop)
    ]
