# Generated by Django 3.2.20 on 2024-12-04 11:56

import bluebottle.files.fields
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0009_auto_20231107_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relatedimage',
            name='image',
            field=bluebottle.files.fields.ImageField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.image'),
        ),
    ]
