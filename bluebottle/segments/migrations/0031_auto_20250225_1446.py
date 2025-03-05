# Generated by Django 3.2.20 on 2025-02-25 13:46

import json
from django.db import migrations

def convert_to_quill(apps, schema_editor):
    Segment = apps.get_model('segments', 'Segment')

    for segment in Segment.objects.all(): 
        segment.story = json.dumps({"html": segment.story, "delta": ""})
        segment.save()



class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0030_auto_20230620_1513'),
    ]

    operations = [
        migrations.RunPython(convert_to_quill, migrations.RunPython.noop)
    ]
