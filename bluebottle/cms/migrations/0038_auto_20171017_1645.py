# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-17 14:45


from django.db import migrations, models
import parler


def set_title(apps, schema_editor):
    Stat = apps.get_model('cms', 'Stat')
    StatTranslation = apps.get_model('cms', 'StatTranslation')

    for stat in Stat.objects.all():
        try:
            translation = StatTranslation.objects.get(
                language_code=stat.block.language_code,
                master=stat
            )
            stat.temp_title = translation.title
            stat.save()
        except StatTranslation.DoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0037_auto_20171017_1645'),
    ]

    operations = [
        migrations.RunPython(set_title)
    ]
