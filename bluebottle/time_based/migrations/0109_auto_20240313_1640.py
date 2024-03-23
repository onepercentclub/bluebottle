# Generated by Django 3.2.20 on 2024-03-13 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0108_auto_20240313_1612"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scheduleslot",
            name="end",
        ),
        migrations.AddField(
            model_name="scheduleslot",
            name="duration",
            field=models.DurationField(blank=True, null=True, verbose_name="duration"),
        ),
    ]