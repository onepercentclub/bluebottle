# Generated by Django 2.2.24 on 2022-09-01 07:32

from django.db import migrations


def remove_location_widgets(apps, schema_editor):
    UserDashboardModule = apps.get_model('dashboard', 'UserDashboardModule')
    UserDashboardModule.objects.filter(
        module__in=[
            'bluebottle.initiatives.dashboard.MyOfficeInitiatives',
            'bluebottle.initiatives.dashboard.MyOfficeSubRegionInitiatives',
            'bluebottle.initiatives.dashboard.MyOfficeRegionInitiatives'
        ]
    ).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0039_auto_20220316_1253'),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop,
            migrations.RunPython.noop
        )
    ]
