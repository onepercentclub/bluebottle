# Generated by Django 2.2.24 on 2021-11-22 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0006_auto_20210914_1134'),
    ]

    operations = [
        migrations.AddField(
            model_name='segment',
            name='slug',
            field=models.CharField(max_length=255, null=True, verbose_name='slug'),
        ),
    ]
