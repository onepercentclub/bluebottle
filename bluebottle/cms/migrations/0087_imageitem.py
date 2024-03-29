# Generated by Django 2.2.24 on 2023-03-08 14:13

import bluebottle.utils.validators
from django.db import migrations, models
import django.db.models.deletion
import fluent_contents.extensions


class Migration(migrations.Migration):

    dependencies = [
        ('fluent_contents', '0001_initial'),
        ('cms', '0086_auto_20230301_1333'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageItem',
            fields=[
                ('contentitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fluent_contents.ContentItem')),
                ('title', models.CharField(blank=True, max_length=50, null=True)),
                ('sub_title', models.CharField(blank=True, max_length=400, null=True)),
                ('image', fluent_contents.extensions.PluginImageField(validators=[bluebottle.utils.validators.FileMimetypeValidator(['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'], None, 'invalid_mimetype'), bluebottle.utils.validators.validate_file_infection], verbose_name='Image')),
            ],
            options={
                'verbose_name': 'Image',
                'verbose_name_plural': 'Image',
                'db_table': 'contentitem_cms_imageitem',
            },
            bases=('fluent_contents.contentitem',),
        ),
    ]
