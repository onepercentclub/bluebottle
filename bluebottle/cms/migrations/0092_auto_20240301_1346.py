# Generated by Django 3.2.20 on 2024-03-01 12:46

import bluebottle.utils.validators
from django.db import migrations, models
import fluent_contents.extensions


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0091_auto_20240301_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageplaintextitem',
            name='video_url',
            field=models.URLField(blank=True, max_length=255, null=True, verbose_name='Video URL'),
        ),
        migrations.AlterField(
            model_name='imageplaintextitem',
            name='image',
            field=fluent_contents.extensions.PluginImageField(blank=True, null=True, validators=[bluebottle.utils.validators.FileMimetypeValidator(['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'], None, 'invalid_mimetype'), bluebottle.utils.validators.validate_file_infection], verbose_name='Image'),
        ),
    ]