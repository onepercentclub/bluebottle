# Generated by Django 4.2.17 on 2025-03-10 10:28

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0013_alter_document_owner_alter_image_owner_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("initiatives", "0056_merge_0055_auto_20250122_1142_0055_auto_20250225_1433"),
    ]

    operations = [
        migrations.AddField(
            model_name="initiativeplatformsettings",
            name="enable_reviewing",
            field=models.BooleanField(
                default=True,
                help_text="Enable reviewing of initiatives and activities before they can be published.",
                verbose_name="Enable reviewing",
            ),
        ),
    ]
