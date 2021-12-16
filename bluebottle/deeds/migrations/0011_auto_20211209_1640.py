# Generated by Django 2.2.24 on 2021-12-09 15:40

from django.db import migrations


def fix_participant_dates(apps, schema_editor):
    EffortContribution = apps.get_model('activities', 'EffortContribution')
    EffortContribution.objects.update(end=None)


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0010_auto_20211208_0833'),
    ]

    operations = [
        migrations.RunPython(
            fix_participant_dates,
            migrations.RunPython.noop
        )
    ]
