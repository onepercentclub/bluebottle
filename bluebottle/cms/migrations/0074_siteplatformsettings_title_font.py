# Generated by Django 2.2.24 on 2023-01-06 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0073_auto_20230106_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteplatformsettings',
            name='title_font',
            field=models.FileField(blank=True, help_text='Font to use for titles', null=True, upload_to='', verbose_name='Title font'),
        ),
    ]