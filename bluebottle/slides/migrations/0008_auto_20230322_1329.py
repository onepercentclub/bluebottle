# Generated by Django 2.2.24 on 2023-03-22 12:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('slides', '0007_auto_20200903_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='slide',
            name='image',
        ),
        migrations.RemoveField(
            model_name='slide',
            name='style',
        ),
    ]