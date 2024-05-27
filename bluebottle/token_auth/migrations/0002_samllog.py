# Generated by Django 3.2.20 on 2024-05-14 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("token_auth", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SAMLLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("body", models.TextField()),
                ("created", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]