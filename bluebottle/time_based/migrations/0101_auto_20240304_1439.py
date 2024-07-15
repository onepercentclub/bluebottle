# Generated by Django 3.2.20 on 2024-03-04 13:39

from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.db import migrations
from django.utils.timezone import now, get_current_timezone


def migrate_periodic_activities(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")

    PeriodActivity = apps.get_model("time_based", "PeriodActivity")
    PeriodicActivity = apps.get_model("time_based", "PeriodicActivity")
    periodic_activity_ctype = ContentType.objects.get_for_model(PeriodicActivity)

    activities = PeriodActivity.objects.exclude(duration_period="overall").exclude(
        team_activity="teams"
    )

    for activity in activities:
        print(
            f"Migrating {activity.pk} start={activity.start}, deadline={activity.deadline} duration={activity.duration}"
        )
        periodic_activity = PeriodicActivity(
            timebasedactivity_ptr=activity.timebasedactivity_ptr,
            start=activity.start,
            deadline=activity.deadline,
            is_online=activity.is_online,
            location=activity.location,
            location_hint=activity.location_hint,
            duration=activity.duration,
            period=activity.duration_period,
        )
        periodic_activity.save_base(raw=True)

    PeriodicActivity.objects.update(polymorphic_ctype=periodic_activity_ctype)


def migrate_periodic_participants(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")

    Contribution = apps.get_model("activities", "Contribution")
    PeriodicActivity = apps.get_model("time_based", "PeriodicActivity")
    PeriodicRegistration = apps.get_model("time_based", "PeriodicRegistration")
    PeriodicSlot = apps.get_model("time_based", "PeriodicSlot")
    PeriodicParticipant = apps.get_model("time_based", "PeriodicParticipant")

    PeriodParticipant = apps.get_model("time_based", "PeriodParticipant")
    activities = PeriodicActivity.objects.all()

    period_participant_ctype = ContentType.objects.get_for_model(PeriodParticipant)
    periodic_participant_ctype = ContentType.objects.get_for_model(PeriodicParticipant)
    periodic_registration_ctype = ContentType.objects.get_for_model(PeriodicRegistration)

    for activity in activities:
        tz = get_current_timezone()

        start = tz.localize(
            datetime.combine(
                activity.start or activity.created, datetime.min.replace(hour=0).time()
            )
        )
        deadline = tz.localize(
            datetime.combine(
                activity.deadline or now(),
                datetime.min.replace(hour=23, minute=23).time(),
            )
        )

        if activity.period:
            until = deadline
            if deadline > now():
                until = now()
            while start < until:
                end = start + relativedelta(**{activity.period: 1})

                PeriodicSlot.objects.create(
                    activity=activity,
                    start=start,
                    end=end,
                    duration=activity.duration,
                    status="finished" if end < now() else "running",
                )
                start = end

            for participant in activity.contributors.filter(
                polymorphic_ctype=period_participant_ctype
            ):
                registration_status_map = {
                    "new": "new",
                    "accepted": "accepted",
                    "rejected": "rejected",
                    "withdrawn": "stopped",
                }
                registration = None

                if participant.user:
                    registration, _created = PeriodicRegistration.objects.get_or_create(
                        user=participant.user,
                        activity=activity,
                        status=registration_status_map.get(
                            participant.status, "accepted"
                        ),
                        created=participant.created,
                        polymorphic_ctype=periodic_registration_ctype,
                    )

                for contribution in participant.contributions.filter(
                    timecontribution__contribution_type="period"
                ):
                    slot = PeriodicSlot.objects.filter(
                        start__lte=contribution.start,
                        end__gt=contribution.start,
                        activity=activity,
                    ).first()

                    if not slot:
                        slot = PeriodicSlot.objects.create(
                            created=contribution.created,
                            start=contribution.start,
                            end=contribution.end,
                            activity=activity,
                            duration=activity.duration,
                            status="finished",
                        )

                    participant_status_map = {"failed": "withdrawn"}

                    periodic_participant = PeriodicParticipant.objects.create(
                        slot=slot,
                        created=contribution.created,
                        registration=registration,
                        user=participant.user,
                        activity=activity,
                        status=participant_status_map.get(
                            contribution.status, contribution.status
                        ),
                        polymorphic_ctype=periodic_participant_ctype,
                    )

                    contribution.contributor = periodic_participant
                    contribution.save()

                try:
                    if registration:
                        preparation = participant.contributions.get(
                            timecontribution__contribution_type="preparation"
                        )
                        preparation.contributor = (
                            registration.periodicparticipant_set.order_by(
                                "slot__start"
                            ).first()
                        )
                        preparation.save()
                except Contribution.DoesNotExist:
                    pass

                participant.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("time_based", "0100_auto_20240304_1439"),
    ]

    operations = [
        migrations.RunPython(migrate_periodic_activities, migrations.RunPython.noop),
        migrations.RunPython(migrate_periodic_participants, migrations.RunPython.noop),
    ]
