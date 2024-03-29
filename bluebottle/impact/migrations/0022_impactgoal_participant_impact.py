# Generated by Django 3.2.20 on 2023-09-20 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0021_auto_20221110_1148'),
    ]

    operations = [
        migrations.AddField(
            model_name='impactgoal',
            name='participant_impact',
            field=models.FloatField(blank=True, help_text='Mean impact each participants makes', null=True, verbose_name='impact per participant'),
        ),
    ]
