# Generated by Django 2.2.24 on 2022-03-17 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0045_auto_20211102_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='team_activity',
            field=models.CharField(
                choices=[('teams', 'Teams'), ('individuals', 'Individuals')],
                default='individuals',
                help_text='Is this activity open for individuals or can only teams sign up?',
                max_length=100,
                verbose_name='Team activity'
            ),
        ),
    ]
