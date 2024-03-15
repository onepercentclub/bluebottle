# Generated by Django 3.2.20 on 2024-03-14 13:44

from django.db import migrations



def fix_participant_status(apps, schema_editor):
    PeriodicParticipant = apps.get_model("time_based.PeriodicParticipant")
    PeriodicParticipant.objects.filter(registration__status='accepted').update(status='succeeded')


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0105_activity_types'),
    ]

    operations = [
        migrations.RunPython(fix_participant_status, migrations.RunPython.noop),
    ]
