from colorfield.fields import ColorField
from django.db import migrations, models

import bluebottle.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0103_merge_20250312_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='footer_banner_color',
            field=ColorField(
                verbose_name='Footer banner colour',
                max_length=18,
                null=True,
                blank=True,
                help_text='Background colour for the footer banner'
            ),
        ),
        migrations.AddField(
            model_name='siteplatformsettings',
            name='footer_banner_logo',
            field=models.ImageField(
                verbose_name='Footer banner logo',
                help_text='Logo shown centered on the footer banner colour',
                null=True,
                blank=True,
                upload_to='site_content/',
                validators=[
                    bluebottle.utils.validators.FileMimetypeValidator(
                        allowed_mimetypes=['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'],
                        message=None,
                        code='invalid_mimetype'
                    ),
                    bluebottle.utils.validators.validate_file_infection
                ]
            ),
        ),
    ]
