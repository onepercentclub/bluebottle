# Generated by Django 3.2.20 on 2024-07-18 14:38

from django.db import migrations



def migrate_team_names(apps, schema_editor):
    Team = apps.get_model("time_based", "Team")

    for team in Team.objects.all():
        captain = team.user
        team.name = 'Team ' + captain.first_name + ' ' + captain.last_name
        team.save()


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0128_auto_20240718_1638'),
    ]

    operations = [
        migrations.RunPython(migrate_team_names, reverse_code=migrations.RunPython.noop),
    ]
