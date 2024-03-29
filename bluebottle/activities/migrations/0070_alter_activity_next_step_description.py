# Generated by Django 3.2.20 on 2023-10-09 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0069_auto_20231009_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='next_step_description',
            field=models.TextField(blank=True, default='', help_text='A description to explain what the next step is', null=True, verbose_name='Next step description'),
        ),
    ]
