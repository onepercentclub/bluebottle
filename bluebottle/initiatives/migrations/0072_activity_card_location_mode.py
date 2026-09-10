from django.db import migrations, models


def set_card_location_mode(apps, schema_editor):
    InitiativePlatformSettings = apps.get_model('initiatives', 'InitiativePlatformSettings')
    InitiativePlatformSettings.objects.update(card_location_display='city_country')


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0071_merge_20260713_1539'),
    ]

    operations = [
        migrations.RunPython(set_card_location_mode, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='card_location_display',
            field=models.CharField(
                choices=[
                    ('neighbourhood', 'Neighbourhood'),
                    ('city', 'City'),
                    ('city_region', 'City + region'),
                    ('city_country', 'City + country'),
                ],
                default='city_country',
                help_text=(
                    'Choose how locations appear on activity cards. '
                    'Activity detail pages always show the full location.'
                ),
                max_length=32,
                verbose_name='Activity card location',
            ),
        ),
    ]
