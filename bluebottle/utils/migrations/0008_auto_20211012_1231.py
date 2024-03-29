# Generated by Django 2.2.24 on 2021-10-12 10:31

from django.db import migrations, models
import django.db.models.deletion
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0007_auto_20210825_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translationplatformsettingstranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='utils.TranslationPlatformSettings'),
        ),
        migrations.AlterField(
            model_name='translationplatformsettingstranslation',
            name='office',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Office'),
        ),
        migrations.AlterField(
            model_name='translationplatformsettingstranslation',
            name='office_location',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Office location'),
        ),
        migrations.AlterField(
            model_name='translationplatformsettingstranslation',
            name='select_an_office_location',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Select an office location'),
        ),
        migrations.AlterField(
            model_name='translationplatformsettingstranslation',
            name='whats_the_location_of_your_office',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='What’s the location of your office?'),
        ),
    ]
