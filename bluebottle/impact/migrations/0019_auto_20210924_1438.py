# Generated by Django 2.2.20 on 2021-09-24 12:38

from django.db import migrations, models
import django.db.models.deletion
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0018_auto_20210920_1307'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='impactgoal',
            name='coupled_with_contributions',
        ),
    ]
