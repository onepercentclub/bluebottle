# Generated by Django 2.2.24 on 2022-11-09 14:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0042_auto_20220928_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiativeplatformsettings',
            name='default_office_restriction',
            field=models.CharField(blank=True, choices=[('office', 'Open to people from the same office'), ('office_subregion', 'Open to people from offices within the same group'), ('office_region', 'Open to people from offices within the same region'), ('all', 'Open to people from any office')], default='all', max_length=100, null=True, verbose_name='Default office restriction'),
        ),
    ]