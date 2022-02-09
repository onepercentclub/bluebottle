# Generated by Django 2.2.24 on 2022-02-09 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0045_auto_20211102_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='effortcontribution',
            name='contribution_type',
            field=models.CharField(choices=[('organizer', 'Activity Organizer'), ('deed', 'Deed particpant')], max_length=20, verbose_name='Contribution type'),
        ),
    ]
