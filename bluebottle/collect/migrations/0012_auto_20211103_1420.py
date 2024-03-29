# Generated by Django 2.2.24 on 2021-11-03 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collect', '0011_auto_20211102_1649'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectactivity',
            name='enable_impact',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='collecttypetranslation',
            name='unit_plural',
            field=models.CharField(blank=True, max_length=100, verbose_name='unit plural'),
        ),
    ]
