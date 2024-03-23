# Generated by Django 3.2.20 on 2024-03-04 12:41

from django.db import migrations


def migrate_deadline_activities(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")

    PeriodActivity = apps.get_model("time_based", "PeriodActivity")
    DeadlineActivity = apps.get_model("time_based", "DeadlineActivity")
    deadline_activity_ctype = ContentType.objects.get_for_model(DeadlineActivity)

    activities = PeriodActivity.objects.filter(
        duration_period="overall", team_activity="individuals"
    )

    for activity in activities:
        print(
            f"Migrating {activity.pk} start={activity.start}, deadline={activity.deadline} duration={activity.duration}"
        )
        deadline_activity = DeadlineActivity(
            timebasedactivity_ptr=activity.timebasedactivity_ptr,
            start=activity.start,
            deadline=activity.deadline,
            is_online=activity.is_online,
            location=activity.location,
            location_hint=activity.location_hint,
            duration=activity.duration,
        )
        deadline_activity.save_base(raw=True)

    DeadlineActivity.objects.update(polymorphic_ctype=deadline_activity_ctype)


def migrate_deadline_participants(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")

    DeadlineActivity = apps.get_model("time_based", "DeadlineActivity")
    DeadlineRegistration = apps.get_model("time_based", "DeadlineRegistration")
    DeadlineParticipant = apps.get_model("time_based", "DeadlineParticipant")

    PeriodParticipant = apps.get_model("time_based", "PeriodParticipant")
    activities = DeadlineActivity.objects.all()

    period_participant_ctype = ContentType.objects.get_for_model(PeriodParticipant)
    deadline_participant_ctype = ContentType.objects.get_for_model(DeadlineParticipant)
    deadline_registration_ctype = ContentType.objects.get_for_model(DeadlineRegistration)

    for activity in activities:
        for participant in activity.contributors.filter(
            polymorphic_ctype=period_participant_ctype, user__isnull=False
        ):
            registration, _created = DeadlineRegistration.objects.get_or_create(
                user=participant.user,
                activity=activity,
                polymorphic_ctype=deadline_registration_ctype,
                status="new" if participant.status == "new" else "accepted",
            )
            deadline_participant = DeadlineParticipant.objects.create(
                registration=registration,
                user=participant.user,
                activity=activity,
                status=participant.status,
                polymorphic_ctype=deadline_participant_ctype,
            )
            participant.contributions.update(contributor=deadline_participant)
            participant.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0098_merge_20240226_1501"),
    ]

    operations = [
        migrations.RunPython(migrate_deadline_activities, migrations.RunPython.noop),
        migrations.RunPython(migrate_deadline_participants, migrations.RunPython.noop),
    ]
