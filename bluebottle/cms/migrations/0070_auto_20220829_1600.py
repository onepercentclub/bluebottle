# Generated by Django 2.2.24 on 2022-08-29 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0069_step_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='external',
            field=models.BooleanField(default=False, help_text='Open the link in a new browser tab', verbose_name='Open in new tab'),
        ),
        migrations.AlterField(
            model_name='step',
            name='link',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Link'),
        ),
    ]