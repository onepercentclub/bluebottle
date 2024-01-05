# Generated by Django 3.2.20 on 2023-12-06 10:16

from django.db import migrations

def set_slot_selection_to_free(apps, schema_editor):
    DateActivity = apps.get_model('time_based', 'DateActivity')
    DateActivity.objects.update(slot_selection='free')

class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0079_auto_20231012_0803'),
    ]

    operations = [
        migrations.RunPython(set_slot_selection_to_free),
    ]