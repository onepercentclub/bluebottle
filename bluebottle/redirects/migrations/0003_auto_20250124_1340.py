# Generated by Django 3.2.20 on 2025-01-24 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('redirects', '0002_auto_20230710_1313'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='redirect',
            options={'ordering': ('old_path',), 'verbose_name': 'redirect', 'verbose_name_plural': 'redirects'},
        ),
        migrations.RemoveField(
            model_name='redirect',
            name='fallback_redirect',
        ),
        migrations.RemoveField(
            model_name='redirect',
            name='nr_times_visited',
        ),
    ]
