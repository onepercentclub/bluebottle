# Generated by Django 3.2.20 on 2023-09-21 09:32

import bluebottle.cms.models
import bluebottle.utils.fields
import bluebottle.utils.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0089_auto_20230413_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageplaintextitem',
            name='action_link',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='imageplaintextitem',
            name='action_text',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='siteplatformsettings',
            name='body_font',
            field=models.FileField(blank=True, help_text='Font to use for paragraph texts. Should be .woff2 type. Deprecated: Do not override body font for new tenants', null=True, upload_to='', validators=[bluebottle.cms.models.SitePlatformSettings.validate_file_extension], verbose_name='Body font'),
        ),
        migrations.AlterField(
            model_name='step',
            name='image',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='The image will be displayed in a square. Upload a square or round image with equal height, to prevent your image from being cropped.', max_length=255, null=True, upload_to='step_images/', validators=[bluebottle.utils.validators.FileMimetypeValidator(['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'], None, 'invalid_mimetype'), bluebottle.utils.validators.validate_file_infection], verbose_name='Image'),
        ),
    ]
