# Generated by Django 3.2.19 on 2023-07-24 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0004_update_created'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='update',
            options={'verbose_name': 'Update'},
        ),
        migrations.AddField(
            model_name='update',
            name='notify',
            field=models.BooleanField(default=False, verbose_name='notify supporters'),
        ),
    ]
