from django.db.models import Count, OuterRef, Q, Subquery

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectContribution, CollectContributor
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
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


def _participant_pks(participant_model, **filters):
    return participant_model.objects.filter(**filters).values('pk')


def _contrib_filter(participant_model, **participant_filters):
    """Match contributions to a concrete participant type (subclass fields allowed)."""
    return {'contributor_id__in': _participant_pks(participant_model, **participant_filters)}


def _exclude_valid_participants(queryset, participant_model, **valid_state):
    """Exclude rows whose contributor matches all participant filters (AND)."""
    return queryset.exclude(contributor_id__in=_participant_pks(participant_model, **valid_state))


def _activities_with_participants(participant_model, **participant_filters):
    return {
        'id__in': participant_model.objects.filter(**participant_filters).values('activity_id'),
    }


def run(*args):
    fix = 'fix' in args
    verbose = 'verbose' in args
    total_errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):

            date_participants_without_registration = DateParticipant.objects.filter(
                registration__isnull=True,
                user__isnull=False,
                slot__isnull=False
            )
            succeeded_date_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='succeeded',
                    **_contrib_filter(
                        DateParticipant,
                        user__isnull=False,
                        registration__isnull=False,
                    ),
                ),
                DateParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('succeeded', 'new', 'accepted'),
                activity__status__in=('open', 'succeeded', 'full'),
            )
            succeeded_periodic_contributions = TimeContribution.objects.filter(
                status='succeeded',
                **_contrib_filter(PeriodicParticipant),
            ).exclude(
                Q(contributor_id__in=_participant_pks(
                    PeriodicParticipant, registration__status__in=('accepted', 'new'),
                ))
                | Q(contributor_id__in=_participant_pks(
                    PeriodicParticipant, status__in=('succeeded', 'new', 'accepted'),
                ))
                | Q(contributor_id__in=_participant_pks(
                    PeriodicParticipant, activity__status__in=('open', 'succeeded', 'full'),
                ))
            )
            succeeded_deadline_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='succeeded',
                    **_contrib_filter(DeadlineParticipant, user__isnull=False),
                ),
                DeadlineParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('succeeded', 'new', 'accepted'),
                activity__status__in=('open', 'succeeded', 'full'),
            )

            succeeded_schedule_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='succeeded',
                    **_contrib_filter(
                        ScheduleParticipant, activity__team_activity='individuals',
                    ),
                ),
                ScheduleParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('succeeded', 'new', 'accepted', 'scheduled', 'unscheduled'),
                activity__status__in=('open', 'succeeded', 'full'),
            )
            succeeded_team_schedule_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='succeeded',
                    **_contrib_filter(
                        TeamScheduleParticipant, activity__team_activity='teams',
                    ),
                ),
                TeamScheduleParticipant,
                team_member__status__in=('active',),
                team_member__team__status__in=('succeeded', 'scheduled', 'accepted'),
                status__in=('succeeded', 'new', 'accepted', 'scheduled'),
                activity__status__in=('open', 'succeeded', 'full'),
            )
            succeeded_contributions = (
                succeeded_date_contributions |
                succeeded_periodic_contributions |
                succeeded_schedule_contributions |
                succeeded_deadline_contributions |
                succeeded_team_schedule_contributions
            )

            new_failed_date_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='new',
                    **_contrib_filter(
                        DateParticipant,
                        user__isnull=False,
                        registration__isnull=False,
                    ),
                ),
                DateParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('new', 'succeeded', 'accepted'),
                activity__status__in=(
                    'draft', 'submitted', 'needs_work', 'open', 'new', 'full', 'succeeded',
                ),
            )
            new_failed_periodic_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='new',
                    **_contrib_filter(PeriodicParticipant),
                ),
                PeriodicParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('new', 'accepted', 'succeeded'),
                activity__status__in=(
                    'draft', 'submitted', 'needs_work', 'open', 'new', 'full', 'succeeded',
                ),
            )
            new_failed_deadline_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='new',
                    **_contrib_filter(DeadlineParticipant, user__isnull=False),
                ),
                DeadlineParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('new', 'succeeded', 'accepted'),
                activity__status__in=(
                    'draft', 'submitted', 'needs_work', 'open', 'new', 'full', 'succeeded',
                ),
            )

            new_failed_schedule_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='new',
                    **_contrib_filter(
                        ScheduleParticipant, activity__team_activity='individuals',
                    ),
                ),
                ScheduleParticipant,
                registration__status__in=('accepted', 'new'),
                status__in=('new', 'succeeded', 'accepted', 'scheduled', 'unscheduled'),
                activity__status__in=(
                    'draft', 'submitted', 'needs_work', 'open', 'new', 'full', 'succeeded',
                ),
            )
            new_failed_team_schedule_contributions = _exclude_valid_participants(
                TimeContribution.objects.filter(
                    status='new',
                    **_contrib_filter(
                        TeamScheduleParticipant, activity__team_activity='teams',
                    ),
                ),
                TeamScheduleParticipant,
                team_member__status__in=('active',),
                team_member__team__status__in=('new', 'scheduled', 'accepted'),
                status__in=('new', 'succeeded', 'accepted', 'scheduled'),
                activity__status__in=(
                    'draft', 'submitted', 'needs_work', 'open', 'new', 'full', 'succeeded',
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
                **_contrib_filter(
                    DateParticipant,
                    user__isnull=False,
                    status__in=('new', 'accepted', 'registered', 'succeeded'),
                    registration__status__in=('accepted',),
                    activity__status__in=('succeeded',),
                ),
            )

            new_succeeded_deadline_contributions = TimeContribution.objects.filter(
                status='new',
                **_contrib_filter(
                    DeadlineParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'succeeded', 'registered'),
                    registration__status__in=('accepted',),
                    activity__status__in=('succeeded',),
                ),
            )
            new_succeeded_periodic_contributions = TimeContribution.objects.filter(
                status='new',
                **_contrib_filter(
                    PeriodicParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('accepted', 'stopped'),
                    activity__status__in=('succeeded', 'open'),
                ),
            )

            new_succeeded_schedule_contributions = TimeContribution.objects.filter(
                status='new',
                **_contrib_filter(
                    ScheduleParticipant,
                    activity__team_activity='individuals',
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('accepted', 'stopped'),
                    activity__status__in=('succeeded',),
                ),
            )
            new_succeeded_schedule_team_contributions = TimeContribution.objects.filter(
                status='new',
                **_contrib_filter(
                    TeamScheduleParticipant,
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
                **_contrib_filter(
                    CollectContributor,
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

            failed_date_contributions = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    DateParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'registered', 'succeeded'),
                    registration__status__in=('accepted',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )

            failed_deadline_contributions = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    DeadlineParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'succeeded', 'registered'),
                    registration__status__in=('accepted',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )
            failed_periodic_contributions = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    PeriodicParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('accepted', 'stopped'),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )

            failed_schedule_contributions = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    ScheduleParticipant,
                    activity__team_activity='individuals',
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('accepted', 'stopped'),
                    activity__status__in=('open', 'succeeded'),
                ),
            )
            failed_schedule_team_contributions = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    TeamScheduleParticipant,
                    activity__team_activity='teams',
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('accepted', 'stopped'),
                    activity__status__in=('open', 'succeeded', 'full'),
                    team_member__status__in=('active',),
                    team_member__team__status__in=('succeeded', 'scheduled'),
                ),
            )

            failed_collect_contributions = CollectContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    CollectContributor,
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
                **_contrib_filter(
                    DateParticipant,
                    status__in=('new',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
                slot_participant__status__in=('registered',),
            )
            failed_deadline_contributions_new = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    DeadlineParticipant,
                    user__isnull=False,
                    status__in=('new',),
                    registration__status__in=('new',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )
            failed_periodic_contributions_new = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    PeriodicParticipant,
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('new',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )

            failed_schedule_contributions_new = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    ScheduleParticipant,
                    activity__team_activity='individuals',
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('new',),
                    activity__status__in=('open', 'succeeded', 'full'),
                ),
            )
            failed_schedule_team_contributions_new = TimeContribution.objects.filter(
                status='failed',
                **_contrib_filter(
                    TeamScheduleParticipant,
                    activity__team_activity='teams',
                    user__isnull=False,
                    status__in=('accepted', 'stopped'),
                    registration__status__in=('new',),
                    activity__status__in=('open', 'succeeded', 'full'),
                    team_member__status__in=('active',),
                    team_member__team__status__in=('new', 'succeeded', 'scheduled'),
                ),
            )

            failed_contributions_new = (
                failed_date_contributions_new |
                failed_deadline_contributions_new |
                failed_periodic_contributions_new |
                failed_schedule_contributions_new |
                failed_schedule_team_contributions_new
            )

            _slots_per_activity = (
                DateActivitySlot.objects.filter(activity_id=OuterRef('activity_id'))
                .values('activity_id')
                .annotate(cnt=Count('id'))
                .values('cnt')
            )
            registrations_without_participant = (
                DateRegistration.objects.filter(
                    status='accepted',
                    participants__isnull=True,
                    activity_id__in=DateActivity.objects.values('pk'),
                )
                .annotate(slot_count=Subquery(_slots_per_activity))
                .filter(slot_count=1)
            )

            errors = (
                failed_time_contributions.count() or
                failed_collect_contributions.count() or
                succeeded_contributions.count() or
                failed_contributions_new.count() or
                registrations_without_participant.count() or
                date_participants_without_registration.count() or
                new_should_be_failed.count() or
                new_succeeded_collect_contributions.count()
            )
            if errors:
                total_errors = True

                print("### Tenant {}:".format(client.name))
                failed_count = (
                    failed_time_contributions.count() + failed_collect_contributions.count()
                )
                if failed_count:
                    print(f'failed or new but should be succeeded: {failed_count}')
                    if verbose:
                        failed_ids = (
                            [str(c.id) for c in failed_time_contributions]
                            + [str(c.id) for c in failed_collect_contributions]
                        )
                        print(f'IDs: {" ".join(failed_ids)}')
                if failed_contributions_new.count():
                    print(f'failed but should be new: {failed_contributions_new.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in failed_contributions_new])}')
                if succeeded_contributions.count():
                    print(f'succeeded but should be failed: {succeeded_contributions.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in succeeded_contributions])}')
                if new_should_be_failed.count():
                    print(f'new but should be failed: {new_should_be_failed.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in new_should_be_failed])}')
                if new_should_be_succeeded.count():
                    print(f'new but should be succeeded: {new_should_be_succeeded.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(c.id) for c in new_should_be_succeeded])}')
                if registrations_without_participant.count():
                    print(f'registrations without participant (single slot): '
                          f'{registrations_without_participant.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(r.id) for r in registrations_without_participant])}')
                if date_participants_without_registration.count():
                    print(f'date participants without registration: '
                          f'{date_participants_without_registration.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(p.id) for p in date_participants_without_registration])}')
                if new_succeeded_collect_contributions.count():
                    print(f'new collect but should be succeeded: {new_succeeded_collect_contributions.count()}')
                    if verbose:
                        print(f'IDs: {" ".join([str(p.id) for p in new_succeeded_collect_contributions])}')

                print('\n')
                if fix:
                    DeadlineParticipant.objects.filter(status='stopped').update(status='succeeded')
                    for participant in DeadlineParticipant.objects.filter(registration__isnull=True):
                        if participant.user:
                            participant.registration = DeadlineRegistration.objects.create(
                                activity=participant.activity, status="accepted", user=participant.user
                            )
                            participant.save()

                    for activity in DeadlineActivity.objects.filter(
                        **_activities_with_participants(
                            DeadlineParticipant,
                            status__in=('succeeded',),
                        ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work'),
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in ScheduleActivity.objects.filter(
                        **_activities_with_participants(
                            ScheduleParticipant,
                            status__in=('succeeded',),
                        ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work'),
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in ScheduleActivity.objects.filter(
                        **_activities_with_participants(
                            TeamScheduleParticipant,
                            status__in=('succeeded',),
                        ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work'),
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in PeriodicActivity.objects.filter(
                        **_activities_with_participants(
                            PeriodicParticipant,
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

    if not fix and total_errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")
    if not verbose and total_errors:
        print("☝️ Add '--script-args=verbose' to the command to see all related ids of the faulty contributions.")

    if not total_errors:
        print("No errors found! 🎉🎉🎉")
