# Generated by Django 2.2.24 on 2023-06-26 15:20

from django.db import migrations


def set_end_date(apps, schema_editor):
    PeriodActivity = apps.get_model('time_based', 'PeriodActivity')
    PeriodParticipant = apps.get_model('time_based', 'PeriodParticipant')
    for activity in PeriodActivity.objects.filter(status='succeeded', deadline__isnull=True).all():
        contributors = PeriodParticipant.objects.filter(activity_id=activity.id).order_by('-updated')
        if contributors.exists():
            activity.deadline = contributors[0].updated
        else:
            activity.deadline = activity.updated
        activity.save()


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0075_auto_20230127_1552'),
    ]

    operations = [
        migrations.RunPython(
            set_end_date,
            migrations.RunPython.noop
        )
    ]
