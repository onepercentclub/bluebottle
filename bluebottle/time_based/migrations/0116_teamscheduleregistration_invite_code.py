# Generated by Django 3.2.20 on 2024-04-26 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0115_auto_20240426_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamscheduleregistration',
            name='invite_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
