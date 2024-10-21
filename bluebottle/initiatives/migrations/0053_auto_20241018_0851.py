# Generated by Django 3.2.20 on 2024-10-18 06:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initiatives', '0052_auto_20240314_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiative',
            name='has_organization',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
