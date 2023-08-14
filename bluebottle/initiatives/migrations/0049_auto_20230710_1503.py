# Generated by Django 3.2.19 on 2023-07-10 13:03

from django.db import migrations


def add_default_search_filters(apps, schema_editor):
    InitiativePlatformSettings = apps.get_model('initiatives', 'InitiativePlatformSettings')

    ActivitySearchFilter = apps.get_model('initiatives', 'ActivitySearchFilter')
    InitiativeSearchFilter = apps.get_model('initiatives', 'InitiativeSearchFilter')
    Member = apps.get_model('members', 'Member')

    initiative_settings = InitiativePlatformSettings.objects.first()

    if initiative_settings.enable_matching_emails:
        ActivitySearchFilter.objects.get_or_create(settings=initiative_settings, type='distance')
        ActivitySearchFilter.objects.get_or_create(settings=initiative_settings, type='is_online')

    ActivitySearchFilter.objects.update(highlight=True)
    InitiativeSearchFilter.objects.update(highlight=True)

    if initiative_settings.enable_matching_emails:
        # Make sure all users get the pref popup again
        Member.objects.update(matching_options_set=None)


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0048_auto_20230629_0857'),
    ]

    operations = [
        migrations.RunPython(
            add_default_search_filters,
            migrations.RunPython.noop
        )
    ]