# Generated by Django 2.2.24 on 2022-02-09 12:12

import bluebottle.utils.fields
import bluebottle.utils.validators
import colorfield.fields
from django.db import migrations, models
import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0022_auto_20220209_1308'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='segment',
            name='email_domain',
        ),
    ]