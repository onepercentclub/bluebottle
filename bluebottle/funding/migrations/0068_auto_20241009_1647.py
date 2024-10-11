# Generated by Django 3.2.20 on 2024-10-09 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funding', '0067_auto_20241009_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='description',
            field=models.TextField(blank=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='bank_account_logo/', verbose_name='Logo'),
        ),
    ]
