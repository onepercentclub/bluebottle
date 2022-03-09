# Generated by Django 2.2.24 on 2021-12-09 09:01

import bluebottle.utils.fields
import bluebottle.utils.validators
import colorfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0011_segment_story'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segment',
            name='background_color',
            field=colorfield.fields.ColorField(blank=True, default=None, help_text='The text color will automatically be set based on the contrast with the background', max_length=18, null=True, verbose_name='Background color'),
        ),
        migrations.AlterField(
            model_name='segment',
            name='cover_image',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='Cover image, 400x300 px', max_length=255, null=True, upload_to='categories/logos/', validators=[bluebottle.utils.validators.FileMimetypeValidator(['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'], None, 'invalid_mimetype'), bluebottle.utils.validators.validate_file_infection], verbose_name='cover image'),
        ),
        migrations.AlterField(
            model_name='segment',
            name='logo',
            field=bluebottle.utils.fields.ImageField(blank=True, help_text='Logo image. 100x100px', max_length=255, null=True, upload_to='categories/logos/', validators=[bluebottle.utils.validators.FileMimetypeValidator(['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'], None, 'invalid_mimetype'), bluebottle.utils.validators.validate_file_infection], verbose_name='logo'),
        ),
        migrations.AlterField(
            model_name='segment',
            name='story',
            field=models.TextField(blank=True, help_text='Longer explanation, containing the goals of your segment', null=True, verbose_name='Story'),
        ),
        migrations.AlterField(
            model_name='segment',
            name='tag_line',
            field=models.CharField(blank=True, help_text='Short tag line for your segment', max_length=255, null=True, verbose_name='tag line'),
        ),
    ]
