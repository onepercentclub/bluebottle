# Generated by Django 3.2.20 on 2024-09-06 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0096_auto_20240905_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='donatebuttoncontent',
            name='button_text',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
