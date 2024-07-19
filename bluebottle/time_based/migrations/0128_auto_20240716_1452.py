# Generated by Django 3.2.20 on 2024-07-16 12:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0074_alter_contributor_team"),
        ("time_based", "0127_migrate_team_activities"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="team",
            options={
                "permissions": (
                    ("api_read_team", "Can view a team through the API"),
                    ("api_add_team", "Can add a team through the API"),
                    ("api_change_team", "Can change a team through the API"),
                    ("api_delete_team", "Can delete a team through the API"),
                    ("api_read_own_team", "Can view own team through the API"),
                    ("api_add_own_team", "Can add own team through the API"),
                    ("api_change_own_team", "Can change own team through the API"),
                    ("api_delete_own_team", "Can delete own team through the API"),
                ),
                "verbose_name": "Team",
                "verbose_name_plural": "Teams",
            },
        ),
        migrations.AlterField(
            model_name="periodicactivity",
            name="period",
            field=models.CharField(
                blank=True,
                choices=[
                    ("days", "per day"),
                    ("weeks", "per week"),
                    ("months", "per month"),
                ],
                help_text="When should the activity be repeated?",
                max_length=100,
                null=True,
                verbose_name="Period",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="activity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="registrations",
                to="activities.activity",
            ),
        ),
    ]
