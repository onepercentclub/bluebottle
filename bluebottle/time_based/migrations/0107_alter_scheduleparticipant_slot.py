# Generated by Django 3.2.20 on 2024-03-13 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0106_auto_20240312_1744"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scheduleparticipant",
            name="slot",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="participants",
                to="time_based.scheduleslot",
            ),
        ),
    ]