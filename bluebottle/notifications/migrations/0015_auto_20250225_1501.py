# Generated by Django 3.2.20 on 2025-02-25 14:01

import json
from django.db import migrations

def convert_to_quill(apps, schema_editor):
    MessageTemplate = apps.get_model('notifications', 'MessageTemplate')

    for template in MessageTemplate.objects.all(): 
        for translation in template.translations.all():
            translation.body_html = json.dumps({"html": translation.body_html, "delta": ""})
            translation.save()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0014_migrate_periodic_messages'),
    ]

    operations = [
        migrations.RunPython(convert_to_quill, migrations.RunPython.noop)
    ]
