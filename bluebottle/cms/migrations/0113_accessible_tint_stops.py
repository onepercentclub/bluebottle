import colorfield.fields
from django.db import migrations


def backfill_tint_stops(apps, schema_editor):
    SitePlatformSettings = apps.get_model('cms', 'SitePlatformSettings')
    settings = SitePlatformSettings.objects.first()
    if not settings:
        return
    from bluebottle.cms.utils.color_contrast import apply_on_colors
    apply_on_colors(settings)
    settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0112_merge_accessible_colours'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='action_on_tint_100_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a lighter tint of the action colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text on light tint',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='action_on_tint_300_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a stronger tint of the action colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text on strong tint',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='description_on_tint_100_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a lighter tint of the description colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Description text on light tint',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='description_on_tint_300_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a stronger tint of the description colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Description text on strong tint',
            ),
        ),
        migrations.RunPython(backfill_tint_stops, migrations.RunPython.noop),
    ]
