# Generated by Django 3.2.20 on 2024-04-26 09:50

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0114_merge_20240426_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamscheduleslot',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='teamscheduleslot',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='scheduleslot',
            name='start',
            field=models.DateTimeField(null=True, verbose_name='start date and time'),
        ),
        migrations.AlterField(
            model_name='teamscheduleslot',
            name='start',
            field=models.DateTimeField(null=True, verbose_name='start date and time'),
        ),
        migrations.CreateModel(
            name='ScheduleTeamMember',
            fields=[
                ('registration_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='time_based.registration')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_members', to='time_based.registration')),
            ],
            options={
                'verbose_name': 'Team members for schedule activities',
                'verbose_name_plural': 'Team members for schedule activities',
            },
            bases=('time_based.registration',),
        ),
    ]
