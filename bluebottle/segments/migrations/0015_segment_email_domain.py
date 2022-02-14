# Generated by Django 2.2.24 on 2022-01-17 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0014_auto_20211210_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='segment',
            name='email_domain',
            field=models.EmailField(
                blank=True,
                help_text='Users with email addresses for this domain are automatically added to this segment',
                max_length=255, null=True, verbose_name='Email'),
        ),
    ]
