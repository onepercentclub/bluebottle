# Generated by Django 3.2.20 on 2023-10-09 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0068_auto_20230719_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='next_step_description',
            field=models.CharField(blank=True, default='', help_text='A description to explain what the next step is', max_length=300, null=True, verbose_name='Next step description'),
        ),
        migrations.AddField(
            model_name='activity',
            name='next_step_link',
            field=models.URLField(blank=True, default='', help_text='This link is shown after a user joined as the next step for the activity', max_length=100, null=True, verbose_name='Next step link'),
        ),
        migrations.AddField(
            model_name='activity',
            name='next_step_title',
            field=models.CharField(blank=True, default='', help_text='The title on the next link button', max_length=100, null=True, verbose_name='Next step title'),
        ),
    ]