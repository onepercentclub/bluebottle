# Generated by Django 2.2.24 on 2021-11-24 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0010_auto_20211123_1533'),
    ]

    operations = [
        migrations.AddField(
            model_name='segment',
            name='story',
            field=models.TextField(blank=True, verbose_name='Story'),
        ),
    ]
