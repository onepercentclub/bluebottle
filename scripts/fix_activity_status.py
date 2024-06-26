from django.db.models import Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import DateActivity, DateActivitySlot, TimeContribution


def get_open_activities():
    return DateActivity.objects.exclude(
        slots__status='open'
    ).filter(
        status='open'
    ).all()


def get_full_activities():
    return DateActivity.objects.filter(
        slots__status='open',
        status__in=['full', 'succeeded'],
        registration_deadline__isnull=True
    ).all()


def get_full_slots():
    return DateActivitySlot.objects.filter(
        status='full',
        capacity__gt=Count('slot_participants'),
        slot_participants__status='registered',
        slot_participants__participant__status='accepted'
    ).annotate(participants=Count('slot_participants')).all()


def get_open_slots():
    return DateActivitySlot.objects.filter(
        status='open',
        capacity__lte=Count('slot_participants'),
        slot_participants__status='registered',
        slot_participants__participant__status='accepted'
    ).annotate(participants=Count('slot_participants')).all()


def get_succeeded_date_contributions():
    return TimeContribution.objects.filter(
        start__year=2024,
        status='succeeded',
        slot_participant__status__in=['removed', 'withdrawn'],
    ).all()


def get_succeeded_period_contributions():
    return TimeContribution.objects.filter(
        start__year=2024,
        status='succeeded',
        contributor__status__in=['removed', 'withdrawn'],
        contribution_type='period',
    ).all()


def get_failed_date_contributions():
    return TimeContribution.objects.filter(
        start__year=2024,
        status__in=['failed', 'new'],
        slot_participant__status__in=['succeeded', 'registered'],
        slot_participant__slot__status='finished',
        contributor__status__in=['succeeded', 'registered', 'accepted'],
        contributor__activity__status__in=['open', 'full', 'succeeded'],
    ).all()


def get_failed_period_contributions():
    return TimeContribution.objects.filter(
        start__year=2023,
        status__in=['failed', 'new'],
        contribution_type='period',
        contributor__status__in=['succeeded', 'registered', 'accepted'],
        contributor__activity__status__in=['open', 'full', 'succeeded'],
    ).exclude(
        contributor__team__status=['rejected', 'deleted', 'withdrawn']
    ).all()


def run(*args):
    fix = 'fix' in args
    errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):

            full_activities = get_full_activities()
            open_activities = get_open_activities()

            full_slots = get_full_slots()
            open_slots = get_open_slots()

            succeeded_contributions = get_succeeded_date_contributions()
            failed_contributions = get_failed_date_contributions()

            succeeded_period_contributions = get_succeeded_period_contributions()
            failed_period_contributions = get_failed_period_contributions()

            if (
                full_activities.count() > 0 or
                open_activities.count() > 0 or
                full_slots.count() > 0 or
                open_slots.count() > 0 or
                succeeded_contributions.count() > 0 or
                failed_contributions.count() > 0 or
                succeeded_period_contributions.count() > 0 or
                failed_period_contributions.count() > 0
            ):
                errors = True
                print("### Tenant {}:".format(client.name))
            for activity in full_activities:
                print(
                    "Activity [{id}] '{title}' is {status} but there are still open slots.".format(
                        id=activity.id,
                        title=activity.title,
                        status=activity.status
                    )
                )
                if fix:
                    activity.states.reopen(save=True)
            for activity in open_activities:
                print(
                    "Activity [{id}] '{title}' is {status} but there aren't any open slots.".format(
                        id=activity.id,
                        title=activity.title,
                        status=activity.status
                    )
                )
                if fix:
                    activity.states.lock(save=True)

            for slot in full_slots:
                print(
                    "Slot [{id}] for activity '{activity}' is full, but there are spots left. "
                    "Capacity {capacity}, participants {participants}".format(
                        id=slot.id,
                        activity=slot.activity.title,
                        capacity=slot.capacity,
                        participants=slot.participants
                    )
                )
                if fix:
                    slot.states.unlock(save=True)

            for slot in open_slots:
                print(
                    "Slot [{id}] for activity '{activity}' is open, but there aren't any spots left. "
                    "Capacity {capacity}, participants {participants}".format(
                        id=slot.id,
                        activity=slot.activity.title,
                        capacity=slot.capacity,
                        participants=slot.participants
                    )
                )
                if fix:
                    slot.states.lock(save=True)

            if succeeded_contributions.count() > 0:
                print(
                    "Succeeded contributions with failed date participants: "
                    "{count}".format(count=succeeded_contributions.count())
                )

            # for contribution in succeeded_contributions:
            #     print(
            #         "Contribution [{id}] for activity '{activity}' is succeeded, "
            #         "but the participant is {status}.".format(
            #             id=contribution.id,
            #             activity=contribution.slot_participant.slot.activity.title,
            #             status=contribution.slot_participant.status
            #         )
            #     )
            #     if fix:
            #         contribution.states.failed(save=True)

            if succeeded_period_contributions.count() > 0:
                print(
                    "Succeeded contributions with failed period participants: "
                    "{count}".format(count=succeeded_period_contributions.count())
                )

            if failed_contributions.count() > 0:
                print(
                    "Failed contributions with successful participants: "
                    "{count}".format(count=failed_contributions.count())
                )

            # for contribution in failed_contributions:
            #     print(
            #         "Contribution [{id}] for activity '{activity}' is {status}, "
            #         "but the participant is {participant_status}.".format(
            #             id=contribution.id,
            #             status=contribution.status,
            #             activity=contribution.slot_participant.slot.activity.title,
            #             participant_status=contribution.slot_participant.status
            #         )
            #     )
            #     if fix:
            #         contribution.states.failed(save=True)

            if failed_period_contributions.count() > 0:
                print(
                    "Failed contributions with successful period participants: "
                    "{count}".format(count=failed_period_contributions.count())
                )

    if not fix and errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")
    if not errors:
        print("No errors found! 🎉🎉🎉")
