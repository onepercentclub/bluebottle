import colorfield.fields
from django.db import migrations


def backfill_adjusted_colours(apps, schema_editor):
    SitePlatformSettings = apps.get_model('cms', 'SitePlatformSettings')
    settings = SitePlatformSettings.objects.first()
    if not settings or not settings.accessible_colours:
        return
    from bluebottle.cms.utils.color_contrast import apply_on_colors
    apply_on_colors(settings)
    settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0116_siteplatformsettings_accessible_colours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='action_color_adjusted',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Darkened when white or dark text would not be readable on the action colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Adjusted action colour',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='description_color_adjusted',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Darkened when white or dark text would not be readable on the description colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Adjusted description colour',
            ),
        ),
        migrations.RunPython(backfill_adjusted_colours, migrations.RunPython.noop),
    ]
