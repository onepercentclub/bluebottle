# Generated by Django 4.2.17 on 2025-03-05 15:22

import bluebottle.bb_accounts.models
import bluebottle.files.fields
import bluebottle.utils.validators
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0013_alter_document_owner_alter_image_owner_and_more'),
        ('members', '0087_auto_20250305_1621'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='region_manager',
        ),
    ]
