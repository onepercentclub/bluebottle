import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0119_remove_description_tint_stops'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteplatformsettings',
            name='action_text_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Text colour on the action colour. Use white or dark grey, whichever is readable.',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text colour',
            ),
        ),
        migrations.AlterField(
            model_name='siteplatformsettings',
            name='alternative_link_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='The action colour as text on a white or grey background. Use a darker shade if the action colour is too light to read.',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Action text on white',
            ),
        ),
        migrations.AlterField(
            model_name='siteplatformsettings',
            name='description_text_color',
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                help_text='Text colour on the descriptive colour. Use white or dark grey, whichever is readable.',
                max_length=18,
                null=True,
                samples=None,
                verbose_name='Description text colour',
            ),
        ),
    ]
