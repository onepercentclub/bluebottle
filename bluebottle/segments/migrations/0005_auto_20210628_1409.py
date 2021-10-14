# Generated by Django 2.2.20 on 2021-06-28 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0004_auto_20200708_1404'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='segment',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='segmenttype',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='segmenttype',
            name='user_editable',
            field=models.BooleanField(default=True, verbose_name='Editable in user profile'),
        ),
    ]
