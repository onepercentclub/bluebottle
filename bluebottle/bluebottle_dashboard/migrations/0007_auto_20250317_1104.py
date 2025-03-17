# Generated by Django 4.2.20 on 2025-03-17 10:04
from django.db import migrations


def clean_up_orphans(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    member_ids = Member.objects.values_list('id', flat=True)
    UserDashboardModule = apps.get_model('dashboard', 'UserDashboardModule')
    UserDashboardModule.objects.exclude(
        user__in=member_ids
    ).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bluebottle_dashboard', '0006_auto_20250116_1610'),
    ]

    run_before = [
        ('dashboard', '0002_auto_20201228_1929'),
    ]

    operations = [
        migrations.RunPython(clean_up_orphans, migrations.RunPython.noop)
    ]
