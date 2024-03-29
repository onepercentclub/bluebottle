# Generated by Django 3.2.20 on 2023-12-06 10:19
from django.db import migrations


def set_participant_status(apps, schema_editor):
    DateParticipant = apps.get_model('time_based', 'DateParticipant')
    DateParticipant.objects.filter(status__in=('withdrawn', 'succdeeded')).update(status='accepted')
    DateParticipant.objects.filter(status__in=('removed', 'cancelled', 'failed')).update(status='rejected')

class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0080_auto_20231206_1116'),
    ]

    operations = [
        migrations.RunPython(set_participant_status),
    ]
