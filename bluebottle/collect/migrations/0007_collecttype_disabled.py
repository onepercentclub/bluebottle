# Generated by Django 2.2.24 on 2021-09-28 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collect', '0006_auto_20210927_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='collecttype',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]
