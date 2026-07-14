from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiatives', '0072_activity_card_location_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiativeplatformsettings',
            name='card_location_display',
            field=models.CharField(
                choices=[
                    ('neighbourhood', 'Neighbourhood'),
                    ('neighbourhood_city', 'Neighbourhood + city'),
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
