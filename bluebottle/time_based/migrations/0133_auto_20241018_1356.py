# Generated by Django 3.2.20 on 2024-10-18 11:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0035_set_alternate_names'),
        ('time_based', '0132_merge_20240808_1424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timebasedactivity',
            name='review_link',
            field=models.URLField(blank=True, help_text='Direct participants to a questionnaire created from an external website like Microsoft forms.', max_length=2048, null=True, verbose_name='External website link'),
        ),
    ]
