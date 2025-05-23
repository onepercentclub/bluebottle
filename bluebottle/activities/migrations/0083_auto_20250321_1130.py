# Generated by Django 4.2.20 on 2025-03-21 10:30

from django.db import migrations

def migrate_categories(apps, schema_editor):
    Activity = apps.get_model('activities', 'Activity')

    for activity in Activity.objects.select_related(
        'initiative'
    ).prefetch_related(
        'initiative__categories'
    ).all():
        if activity.initiative:
            activity.categories.add(*activity.initiative.categories.all())


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0082_remove_activity_published_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_categories, migrations.RunPython.noop),
    ]
