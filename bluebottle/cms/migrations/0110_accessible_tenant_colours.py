import colorfield.fields
from django.db import migrations


def backfill_accessible_colours(apps, schema_editor):
    SitePlatformSettings = apps.get_model('cms', 'SitePlatformSettings')
    settings = SitePlatformSettings.objects.first()
    if not settings:
        return
    from bluebottle.cms.utils.color_contrast import apply_on_colors
    apply_on_colors(settings)
    settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0109_merge_20251212_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='action_on_tint_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a light tint of the action colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text on tint',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='description_on_background_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so the description colour stays readable as text on white or grey',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Description text on white',
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='description_on_tint_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so text stays readable on a light tint of the description colour',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Description text on tint',
            ),
        ),
        migrations.AlterField(
            model_name='siteplatformsettings',
            name='alternative_link_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Automatically darkened so the action colour stays readable as text on white or grey',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text on white',
            ),
        ),
        migrations.RunPython(backfill_accessible_colours, migrations.RunPython.noop),
    ]
