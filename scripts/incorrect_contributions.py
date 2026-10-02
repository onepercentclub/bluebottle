from django.db.models import Q, Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectContribution, CollectContributor
from bluebottle.time_based.models import (
    DateParticipant,
    DateRegistration,
    DeadlineActivity,
    DeadlineParticipant,
    DeadlineRegistration,
    PeriodicActivity,
    PeriodicParticipant,
    ScheduleActivity,
    ScheduleParticipant,
    TeamScheduleParticipant,
    TimeContribution,
)


def get_buckets():
    """
    Return a dict of querysets with inconsistent records for the current tenant.

    The querysets are lazy: they are evaluated when counted, listed or updated.
    """
    date_participants_without_registration = DateParticipant.objects.filter(
        registration__isnull=True,
        user__isnull=False,
        slot__isnull=False
    )
    succeeded_date_contributions = TimeContribution.objects.filter(
        status='succeeded',
        contributor__in=DateParticipant.objects.filter(
            user__isnull=False,
            registration__isnull=False,
        ),
    ).exclude(
        contributor__in=DateParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('succeeded', 'new', 'accepted'),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    succeeded_periodic_contributions = TimeContribution.objects.filter(
        status='succeeded',
        contributor__in=PeriodicParticipant.objects.all(),
    ).exclude(
        Q(contributor__in=PeriodicParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
        ))
        | Q(contributor__in=PeriodicParticipant.objects.filter(
            status__in=('succeeded', 'new', 'accepted'),
        ))
        | Q(contributor__in=PeriodicParticipant.objects.filter(
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ))
    )
    succeeded_deadline_contributions = TimeContribution.objects.filter(
        status='succeeded',
        contributor__in=DeadlineParticipant.objects.filter(
            user__isnull=False,
        ),
    ).exclude(
        contributor__in=DeadlineParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('succeeded', 'new', 'accepted'),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )

    succeeded_schedule_contributions = TimeContribution.objects.filter(
        status='succeeded',
        contributor__in=ScheduleParticipant.objects.filter(
            activity__team_activity='individuals',
        ),
    ).exclude(
        contributor__in=ScheduleParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('succeeded', 'new', 'accepted', 'scheduled', 'unscheduled'),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    succeeded_team_schedule_contributions = TimeContribution.objects.filter(
        status='succeeded',
        contributor__in=TeamScheduleParticipant.objects.filter(
            activity__team_activity='teams',
        ),
    ).exclude(
        contributor__in=TeamScheduleParticipant.objects.filter(
            team_member__status__in=('active',),
            team_member__team__status__in=('succeeded', 'scheduled', 'accepted'),
            status__in=('succeeded', 'new', 'accepted', 'scheduled'),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    succeeded_contributions = (
        succeeded_date_contributions |
        succeeded_periodic_contributions |
        succeeded_schedule_contributions |
        succeeded_deadline_contributions |
        succeeded_team_schedule_contributions
    )

    new_failed_date_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=DateParticipant.objects.filter(
            user__isnull=False,
            registration__isnull=False,
        ),
    ).exclude(
        contributor__in=DateParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('new', 'succeeded', 'accepted'),
            activity__status__in=(
                'draft', 'submitted', 'needs_work', 'open', 'registration_closed', 'new', 'full', 'succeeded',
            ),
        ),
    )
    new_failed_periodic_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=PeriodicParticipant.objects.all(),
    ).exclude(
        contributor__in=PeriodicParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('new', 'accepted', 'succeeded'),
            activity__status__in=(
                'draft', 'submitted', 'needs_work', 'open', 'registration_closed', 'new', 'full', 'succeeded',
            ),
        ),
    )
    new_failed_deadline_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=DeadlineParticipant.objects.filter(
            user__isnull=False,
        ),
    ).exclude(
        contributor__in=DeadlineParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('new', 'succeeded', 'accepted'),
            activity__status__in=(
                'draft', 'submitted', 'needs_work', 'open', 'registration_closed', 'new', 'full', 'succeeded',
            ),
        ),
    )

    new_failed_schedule_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=ScheduleParticipant.objects.filter(
            activity__team_activity='individuals',
        ),
    ).exclude(
        contributor__in=ScheduleParticipant.objects.filter(
            registration__status__in=('accepted', 'new'),
            status__in=('new', 'succeeded', 'accepted', 'scheduled', 'unscheduled'),
            activity__status__in=(
                'draft', 'submitted', 'needs_work', 'open', 'registration_closed', 'new', 'full', 'succeeded',
            ),
        ),
    )
    new_failed_team_schedule_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=TeamScheduleParticipant.objects.filter(
            activity__team_activity='teams',
        ),
    ).exclude(
        contributor__in=TeamScheduleParticipant.objects.filter(
            team_member__status__in=('active',),
            team_member__team__status__in=('new', 'scheduled', 'accepted'),
            status__in=('new', 'succeeded', 'accepted', 'scheduled'),
            activity__status__in=(
                'draft', 'submitted', 'needs_work', 'open', 'registration_closed', 'new', 'full', 'succeeded',
            ),
        ),
    )
    new_should_be_failed = (
        new_failed_schedule_contributions |
        new_failed_team_schedule_contributions |
        new_failed_schedule_contributions |
        new_failed_deadline_contributions |
        new_failed_date_contributions |
        new_failed_deadline_contributions |
        new_failed_periodic_contributions
    )

    new_succeeded_date_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=DateParticipant.objects.filter(
            user__isnull=False,
            status__in=('new', 'accepted', 'registered', 'succeeded'),
            registration__status__in=('accepted',),
            activity__status__in=('succeeded',),
        ),
    )

    new_succeeded_deadline_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=DeadlineParticipant.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'succeeded', 'registered'),
            registration__status__in=('accepted',),
            activity__status__in=('succeeded',),
        ),
    )
    new_succeeded_periodic_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=PeriodicParticipant.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            slot__status__in=('finished'),
            registration__status__in=('accepted', 'stopped'),
            activity__status__in=('succeeded', 'open', 'registration_closed'),
        ).exclude(
            slot__isnull=True
        ),
    )

    new_succeeded_schedule_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=ScheduleParticipant.objects.filter(
            activity__team_activity='individuals',
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('accepted', 'stopped'),
            activity__status__in=('succeeded',),
        ),
    )
    new_succeeded_schedule_team_contributions = TimeContribution.objects.filter(
        status='new',
        contributor__in=TeamScheduleParticipant.objects.filter(
            activity__team_activity='teams',
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('accepted', 'stopped'),
            activity__status__in=('succeeded',),
            team_member__status__in=('active',),
            team_member__team__status__in=('succeeded', 'scheduled'),
        ),
    )

    new_succeeded_collect_contributions = CollectContribution.objects.filter(
        status='new',
        contributor__in=CollectContributor.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'registered', 'succeeded'),
            activity__status__in=('succeeded',),
        ),
    )

    new_should_be_succeeded = (
        new_succeeded_date_contributions |
        new_succeeded_deadline_contributions |
        new_succeeded_periodic_contributions |
        new_succeeded_schedule_contributions |
        new_succeeded_schedule_team_contributions
    )

    unfinished_date_slot = (
        Q(slot__isnull=True) |
        Q(slot__status__in=('draft', 'open', 'full', 'registration_closed', 'running'))
    )
    unfinished_slot = (
        Q(slot__isnull=True) |
        Q(slot__status__in=('new', 'scheduled', 'running'))
    )

    accepted_date_participants = DateParticipant.objects.filter(
        user__isnull=False,
        status__in=('accepted', 'registered', 'succeeded'),
        registration__status__in=('accepted',),
        activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
    )
    failed_date_contributions = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_date_participants.exclude(unfinished_date_slot),
    )
    failed_date_contributions_unfinished = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_date_participants.filter(unfinished_date_slot),
    )

    failed_deadline_contributions = TimeContribution.objects.filter(
        status='failed',
        contributor__in=DeadlineParticipant.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'succeeded', 'registered'),
            registration__status__in=('accepted',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    accepted_periodic_participants = PeriodicParticipant.objects.filter(
        user__isnull=False,
        status__in=('accepted', 'stopped'),
        registration__status__in=('accepted', 'stopped'),
        activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
    )
    failed_periodic_contributions = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_periodic_participants.exclude(unfinished_slot),
    )
    failed_periodic_contributions_unfinished = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_periodic_participants.filter(unfinished_slot),
    )

    accepted_schedule_participants = ScheduleParticipant.objects.filter(
        activity__team_activity='individuals',
        user__isnull=False,
        status__in=('accepted', 'stopped'),
        registration__status__in=('accepted', 'stopped'),
        activity__status__in=('open', 'registration_closed', 'succeeded'),
    )
    failed_schedule_contributions = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_schedule_participants.exclude(unfinished_slot),
    )
    failed_schedule_contributions_unfinished = TimeContribution.objects.filter(
        status='failed',
        contributor__in=accepted_schedule_participants.filter(unfinished_slot),
    )
    failed_schedule_team_contributions = TimeContribution.objects.filter(
        status='failed',
        contributor__in=TeamScheduleParticipant.objects.filter(
            activity__team_activity='teams',
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('accepted', 'stopped'),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
            team_member__status__in=('active',),
            team_member__team__status__in=('succeeded', 'scheduled'),
        ),
    )

    failed_collect_contributions = CollectContribution.objects.filter(
        status='failed',
        contributor__in=CollectContributor.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'registered', 'succeeded'),
            activity__status__in=('succeeded',),
        ),
    )

    failed_time_contributions = (
        failed_date_contributions |
        failed_deadline_contributions |
        failed_periodic_contributions |
        failed_schedule_contributions |
        failed_schedule_team_contributions
    )

    failed_date_contributions_new = TimeContribution.objects.filter(
        status='failed',
        contributor__in=DateParticipant.objects.filter(
            status__in=('new',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
        slot_participant__status__in=('registered',),
    )
    failed_deadline_contributions_new = TimeContribution.objects.filter(
        status='failed',
        contributor__in=DeadlineParticipant.objects.filter(
            user__isnull=False,
            status__in=('new',),
            registration__status__in=('new',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    failed_periodic_contributions_new = TimeContribution.objects.filter(
        status='failed',
        contributor__in=PeriodicParticipant.objects.filter(
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('new',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )

    failed_schedule_contributions_new = TimeContribution.objects.filter(
        status='failed',
        contributor__in=ScheduleParticipant.objects.filter(
            activity__team_activity='individuals',
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('new',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
        ),
    )
    failed_schedule_team_contributions_new = TimeContribution.objects.filter(
        status='failed',
        contributor__in=TeamScheduleParticipant.objects.filter(
            activity__team_activity='teams',
            user__isnull=False,
            status__in=('accepted', 'stopped'),
            registration__status__in=('new',),
            activity__status__in=('open', 'registration_closed', 'succeeded', 'full'),
            team_member__status__in=('active',),
            team_member__team__status__in=('new', 'succeeded', 'scheduled'),
        ),
    )

    failed_contributions_new = (
        failed_date_contributions_new |
        failed_deadline_contributions_new |
        failed_periodic_contributions_new |
        failed_schedule_contributions_new |
        failed_schedule_team_contributions_new |
        failed_date_contributions_unfinished |
        failed_periodic_contributions_unfinished |
        failed_schedule_contributions_unfinished
    )

    registrations_without_participant = DateRegistration.objects.filter(
        status='accepted',
        participants__isnull=True,
    ).annotate(
        slot_count=Count('activity__timebasedactivity__dateactivity__slots', distinct=True),
    ).filter(
        slot_count=1
    )

    return {
        'failed_time_contributions': failed_time_contributions,
        'failed_collect_contributions': failed_collect_contributions,
        'succeeded_contributions': succeeded_contributions,
        'failed_contributions_new': failed_contributions_new,
        'registrations_without_participant': registrations_without_participant,
        'date_participants_without_registration': date_participants_without_registration,
        'new_should_be_failed': new_should_be_failed,
        'new_should_be_succeeded': new_should_be_succeeded,
        'new_succeeded_collect_contributions': new_succeeded_collect_contributions,
    }


def apply_fixes(buckets):
    """
    Fix the records in `buckets` for the current tenant.

    The order of the updates matters: each update re-evaluates its queryset, so
    earlier updates change what later querysets match.
    """
    failed_time_contributions = buckets['failed_time_contributions']
    failed_collect_contributions = buckets['failed_collect_contributions']
    succeeded_contributions = buckets['succeeded_contributions']
    failed_contributions_new = buckets['failed_contributions_new']
    registrations_without_participant = buckets['registrations_without_participant']
    date_participants_without_registration = buckets['date_participants_without_registration']
    new_should_be_failed = buckets['new_should_be_failed']
    new_should_be_succeeded = buckets['new_should_be_succeeded']
    new_succeeded_collect_contributions = buckets['new_succeeded_collect_contributions']

    DeadlineParticipant.objects.filter(status='stopped').update(status='succeeded')
    for participant in DeadlineParticipant.objects.filter(registration__isnull=True):
        if participant.user:
            participant.registration = DeadlineRegistration.objects.create(
                activity=participant.activity, status="accepted", user=participant.user
            )
            participant.save()

    for activity in DeadlineActivity.objects.filter(
        contributors__in=DeadlineParticipant.objects.filter(
            status__in=('succeeded',),
        ),
        status__in=('expired', 'draft', 'submitted', 'needs_work'),
    ):
        activity.status = 'succeeded'
        activity.save()

    for activity in ScheduleActivity.objects.filter(
        contributors__in=ScheduleParticipant.objects.filter(
            status__in=('succeeded',),
        ),
        status__in=('expired', 'draft', 'submitted', 'needs_work'),
    ):
        activity.status = 'succeeded'
        activity.save()

    for activity in ScheduleActivity.objects.filter(
        contributors__in=TeamScheduleParticipant.objects.filter(
            status__in=('succeeded',),
        ),
        status__in=('expired', 'draft', 'submitted', 'needs_work'),
    ):
        activity.status = 'succeeded'
        activity.save()

    for activity in PeriodicActivity.objects.filter(
        contributors__in=PeriodicParticipant.objects.filter(
            status__in=('succeeded',),
        ),
        status__in=('expired', 'draft', 'submitted', 'needs_work'),
    ):
        activity.status = 'succeeded'
        activity.save()

    succeeded_contributions.update(status='failed')
    new_should_be_failed.update(status='failed')
    new_should_be_succeeded.update(status='succeeded')
    failed_time_contributions.update(status='succeeded')
    failed_collect_contributions.update(status='succeeded')
    failed_contributions_new.update(status='new')
    new_succeeded_collect_contributions.update(status='succeeded')
    for registration in registrations_without_participant.all():
        slot = registration.activity.slots.last()
        participant = DateParticipant(
            send_messages=False,
            slot=slot,
            registration=registration,
            activity=registration.activity,
            user=registration.user
        )
        participant.save()

    def add_participant_to_registration(registration):
        # Check for double registration
        regs = registration.activity.registrations.filter(
            user=registration.user
        ).exclude(id=registration.id)
        if regs.count() > 0:
            print(f"Double registration found for {registration.user} "
                  f"on {registration.activity} removing incomplete one.")
            registration.delete()
            return
        slot = registration.activity.slots.filter(status__in=['open', 'finished']).last()
        if not slot:
            slot = registration.activity.slots.last()
        participant = DateParticipant(
            send_messages=False,
            slot=slot,
            registration=registration,
            activity=registration.activity,
            user=registration.user
        )
        participant.save()

    for registration in registrations_without_participant.all():
        add_participant_to_registration(registration)

    for participant in date_participants_without_registration.all():
        if participant.user:
            registration = DateRegistration(
                send_messages=False,
                activity=participant.activity,
                status="accepted",
                user=participant.user
            )
            registration.save()
            participant.registration = registration
            participant.save()


def run(*args):
    fix = 'fix' in args
    verbose = 'verbose' in args
    total_errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):
            buckets = get_buckets()

            errors = (
                buckets['failed_time_contributions'].count() or
                buckets['failed_collect_contributions'].count() or
                buckets['succeeded_contributions'].count() or
                buckets['failed_contributions_new'].count() or
                buckets['registrations_without_participant'].count() or
                buckets['date_participants_without_registration'].count() or
                buckets['new_should_be_failed'].count() or
                buckets['new_succeeded_collect_contributions'].count()
            )
            if errors:
                total_errors = True

                print("### Tenant {}:".format(client.name))
                failed_should_succeed_count = (
                    buckets['failed_time_contributions'].count() + buckets['failed_collect_contributions'].count()
                )
                if failed_should_succeed_count:
                    print(f'failed or new but should be succeeded: {failed_should_succeed_count}')
                    if verbose:
                        failed_ids = (
                            [str(c.id) for c in buckets['failed_time_contributions']]
                            + [str(c.id) for c in buckets['failed_collect_contributions']]
                        )
                        print(f'IDs: {" ".join(failed_ids)}')
                if buckets['failed_contributions_new'].count():
                    print(f'failed but should be new: {buckets["failed_contributions_new"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in buckets["failed_contributions_new"]])}')
                if buckets['succeeded_contributions'].count():
                    print(f'succeeded but should be failed: {buckets["succeeded_contributions"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in buckets["succeeded_contributions"]])}')
                if buckets['new_should_be_failed'].count():
                    print(f'new but should be failed: {buckets["new_should_be_failed"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in buckets["new_should_be_failed"]])}')
                if buckets['new_should_be_succeeded'].count():
                    print(f'new but should be succeeded: {buckets["new_should_be_succeeded"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in buckets["new_should_be_succeeded"]])}')
                if buckets['registrations_without_participant'].count():
                    print(f'registrations without participant (single slot): '
                          f'{buckets["registrations_without_participant"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(r.id) for r in buckets["registrations_without_participant"]])}')
                if buckets['date_participants_without_registration'].count():
                    print(f'date participants without registration: '
                          f'{buckets["date_participants_without_registration"].count()}')
                    if verbose:
                        ids = [str(p.id) for p in buckets["date_participants_without_registration"]]
                        print(f'IDs: {" ".join(ids)}')
                if buckets['new_succeeded_collect_contributions'].count():
                    print(f'new collect but should be succeeded: '
                          f'{buckets["new_succeeded_collect_contributions"].count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(p.id) for p in buckets["new_succeeded_collect_contributions"]])}')

                print('\n')
                if fix:
                    apply_fixes(buckets)

    if not fix and total_errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")
    if not verbose and total_errors:
        print("☝️ Add '--script-args=verbose' to the command to see all related ids of the faulty contributions.")

    if not total_errors:
        print("No errors found! 🎉🎉🎉")
