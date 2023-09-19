# Generated by Django 3.2.20 on 2023-09-13 09:57

from django.db import migrations


def update_team_contributions(apps, schema_editor):
    TeamSlot = apps.get_model('time_based', 'TeamSlot')
    TimeContribution = apps.get_model('time_based', 'TimeContribution')
    for team_slot in TeamSlot.objects.all():
        TimeContribution.objects.filter(
            contributor__in=team_slot.team.members.all(),
        ).update(start=team_slot.start, value=team_slot.duration)


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0076_auto_20230626_1720'),
    ]

    operations = [
        migrations.RunPython(update_team_contributions, migrations.RunPython.noop),
    ]
