# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25


import bluebottle.utils.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fluent_contents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PictureItem',
            fields=[
                ('contentitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fluent_contents.ContentItem')),
                ('image', bluebottle.utils.fields.ImageField(upload_to=b'content_images', verbose_name='Picture')),
                ('align', models.CharField(choices=[(b'float-left', 'Float left'), (b'center', 'Center'), (b'float-right', 'Float right')], max_length=50, verbose_name='Align')),
            ],
            options={
                'db_table': 'contentitem_contentplugins_pictureitem',
                'verbose_name': 'Picture',
                'verbose_name_plural': 'Pictures',
            },
            bases=('fluent_contents.contentitem',),
        ),
    ]
