# Generated by Django 3.2.20 on 2024-01-05 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0084_auto_20240105_1538"),
    ]

    operations = [
        migrations.AddField(
            model_name="periodactivity",
            name="max_iterations",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="How many times will a participant contribute to this activity?",
                null=True,
                verbose_name="Max iteriations",
            ),
        ),
        migrations.AlterField(
            model_name="periodactivity",
            name="slot_type",
            field=models.CharField(
                choices=[
                    (None, "Not set yet"),
                    (
                        "free",
                        "Anytime. Participants will execute the task on their own time",
                    ),
                    (
                        "tailored",
                        "Tailored. After signing up, participants will be assigned a date and time by the activity manager.",
                    ),
                    (
                        "recurring",
                        "Recurring. Participants are expected to contribute every week or month.",
                    ),
                ],
                default=None,
                help_text="How and when will participants contribute to this activity?",
                max_length=100,
                null=True,
                verbose_name="Time slot type",
            ),
        ),
    ]
