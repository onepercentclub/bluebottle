# Generated by Django 2.2.24 on 2023-01-10 08:18

import bluebottle.cms.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0075_auto_20230110_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='body_font',
            field=models.FileField(blank=True, help_text='Font to use for paragraph texts. Should be .woff2 type', null=True, upload_to='', validators=[bluebottle.cms.models.SitePlatformSettings.validate_file_extension], verbose_name='Body font'),
        ),
    ]
