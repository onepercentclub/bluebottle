# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-02-08 10:19


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_auto_20190129_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='welcome_email_is_sent',
            field=models.BooleanField(default=False, verbose_name='Welcome email is sent'),
        ),
    ]
