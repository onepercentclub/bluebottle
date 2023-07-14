
# Generated by Django 3.2.19 on 2023-07-14 09:20

from django.db import migrations
from django.db.models import F, Func, Value


def migrate_search_distance(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    Member.objects.exclude(search_distance__endswith='km').update(
        search_distance=Func(F('search_distance'), Value('km'), function='CONCAT')
    )

def rollback_search_distance(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    Member.objects.update(search_distance=50)

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0074_auto_20230714_1119'),
    ]

    operations = [
        migrations.RunPython(
            migrate_search_distance,
            rollback_search_distance
        )
    ]
