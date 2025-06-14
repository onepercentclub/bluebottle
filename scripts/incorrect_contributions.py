
from django.db.models import Q, Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import (
    DeadlineActivity, DeadlineRegistration, TimeContribution, DeadlineParticipant,
    ScheduleActivity,
    PeriodicActivity, DateRegistration, DateParticipant
)


def run(*args):
    fix = 'fix' in args
    total_errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):
            succeeded_date_contributions = TimeContribution.objects.filter(
                status='succeeded',
                contributor__dateparticipant__isnull=False,
                contributor__user__isnull=False
            ).exclude(
                Q(contributor__dateparticipant__registration__status__in=('accepted', 'new')) &
                Q(contributor__status__in=('succeeded', 'new', 'accepted')) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )
            succeeded_periodic_contributions = TimeContribution.objects.filter(
                status='succeeded',
                contributor__periodicparticipant__isnull=False
            ).exclude(
                Q(contributor__periodicparticipant__registration__status__in=('accepted', 'new')) |
                Q(contributor__status__in=('succeeded', 'new', 'accepted')) |
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )
            succeeded_deadline_contributions = TimeContribution.objects.filter(
                status='succeeded',
                contributor__deadlineparticipant__isnull=False,
                contributor__user__isnull=False
            ).exclude(
                Q(contributor__deadlineparticipant__registration__status__in=('accepted', 'new')) &
                Q(contributor__status__in=('succeeded', 'new', 'accepted')) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )

            succeeded_schedule_contributions = TimeContribution.objects.filter(
                status='succeeded',
                contributor__scheduleparticipant__isnull=False,
                contributor__activity__team_activity='individuals'
            ).exclude(
                Q(contributor__scheduleparticipant__registration__status__in=('accepted', 'new')) &
                Q(contributor__status__in=('succeeded', 'new', 'accepted')) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )
            succeeded_team_schedule_contributions = TimeContribution.objects.filter(
                status='succeeded',
                contributor__teamscheduleparticipant__isnull=False,
                contributor__activity__team_activity='teams'
            ).exclude(
                Q(contributor__teamscheduleparticipant__team_member__status__in=('active', )) &
                Q(contributor__teamscheduleparticipant__team_member__team__status__in=('succeeded', 'scheduled')) &
                Q(contributor__status__in=('succeeded', 'new', 'accepted')) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )
            succeeded_contributions = (
                succeeded_date_contributions |
                succeeded_periodic_contributions |
                succeeded_schedule_contributions |
                succeeded_deadline_contributions |
                succeeded_team_schedule_contributions
            )

            failed_date_contributions = TimeContribution.objects.filter(
                status='failed',
                contributor__dateparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'registered', 'succeeded'),
                contributor__dateparticipant__registration__status__in=('accepted',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )

            failed_deadline_contributions = TimeContribution.objects.filter(
                status='failed',
                contributor__deadlineparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted',),
                contributor__deadlineparticipant__registration__status__in=('accepted',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )
            failed_periodic_contributions = TimeContribution.objects.filter(
                status='failed',
                contributor__periodicparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__periodicparticipant__registration__status__in=('accepted', 'stopped'),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )

            failed_schedule_contributions = TimeContribution.objects.filter(
                status='failed',
                contributor__activity__team_activity='individuals',
                contributor__scheduleparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__scheduleparticipant__registration__status__in=('accepted', 'stopped'),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )
            failed_schedule_team_contributions = TimeContribution.objects.filter(
                status='failed',
                contributor__activity__team_activity='teams',
                contributor__scheduleparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__scheduleparticipant__registration__status__in=('accepted', 'stopped'),
                contributor__activity__status__in=('open', 'succeeded', 'full',),
                contributor__teamscheduleparticipant__team_member__status__in=('active', ),
                contributor__teamscheduleparticipant__team_member__team__status__in=('succeeded', 'scheduled'),
            )

            failed_contributions = (
                failed_date_contributions |
                failed_deadline_contributions |
                failed_periodic_contributions |
                failed_schedule_contributions |
                failed_schedule_team_contributions
            )

            failed_date_contributions_new = TimeContribution.objects.filter(
                status='failed',
                contributor__dateparticipant__isnull=False,
                contributor__status__in=('new',),
                slot_participant__status__in=('registered',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )
            failed_deadline_contributions_new = TimeContribution.objects.filter(
                status='failed',
                contributor__deadlineparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('new',),
                contributor__deadlineparticipant__registration__status__in=('new',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )
            failed_periodic_contributions_new = TimeContribution.objects.filter(
                status='failed',
                contributor__periodicparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__periodicparticipant__registration__status__in=('new', ),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )

            failed_schedule_contributions_new = TimeContribution.objects.filter(
                status='failed',
                contributor__activity__team_activity='individuals',
                contributor__scheduleparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__scheduleparticipant__registration__status__in=('new',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )
            failed_schedule_team_contributions_new = TimeContribution.objects.filter(
                status='failed',
                contributor__activity__team_activity='teams',
                contributor__scheduleparticipant__isnull=False,
                contributor__user__isnull=False,
                contributor__status__in=('accepted', 'stopped'),
                contributor__scheduleparticipant__registration__status__in=('new', ),
                contributor__activity__status__in=('open', 'succeeded', 'full',),
                contributor__teamscheduleparticipant__team_member__status__in=('active', ),
                contributor__teamscheduleparticipant__team_member__team__status__in=('new', 'succeeded', 'scheduled')
            )

            failed_contributions_new = (
                failed_date_contributions_new |
                failed_deadline_contributions_new |
                failed_periodic_contributions_new |
                failed_schedule_contributions_new |
                failed_schedule_team_contributions_new
            )

            registrations_without_participant = DateRegistration.objects.filter(
                status='accepted',
                participants__isnull=True,
            ).annotate(
                slot_count=Count('activity__timebasedactivity__dateactivity__slots', distinct=True),
            ).filter(
                slot_count=1
            )

            registrations_without_participant_multi_slot = DateRegistration.objects.filter(
                status='accepted',
                participants__isnull=True,
            ).annotate(
                slot_count=Count('activity__timebasedactivity__dateactivity__slots', distinct=True),
            ).filter(
                slot_count__gt=1
            )

            errors = (
                failed_contributions.count() or
                succeeded_contributions.count() or
                failed_contributions_new.count() or
                registrations_without_participant.count() or
                registrations_without_participant_multi_slot.count()
            )
            if errors:
                total_errors = True

                print("### Tenant {}:".format(client.name))
                if failed_contributions.count():
                    print(f'failed but should be succeeded: {failed_contributions.count()}')
                if failed_contributions_new.count():
                    print(f'failed but should be new: {failed_contributions_new.count()}')
                if succeeded_contributions.count():
                    print(f'succeeded but should be failed: {succeeded_contributions.count()}')
                if registrations_without_participant.count():
                    print(f'registrations without participant (single slot): '
                          f'{registrations_without_participant.count()}')
                if registrations_without_participant_multi_slot.count():
                    print(f'registrations without participant (multiple slots): '
                          f'{registrations_without_participant_multi_slot.count()}')

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
                        contributors__deadlineparticipant__status__in=('succeeded', ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work')
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in ScheduleActivity.objects.filter(
                        contributors__scheduleparticipant__status__in=('succeeded', ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work')
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in ScheduleActivity.objects.filter(
                        contributors__teamscheduleparticipant__status__in=('succeeded', ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work')
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    for activity in PeriodicActivity.objects.filter(
                        contributors__periodicparticipant__status__in=('succeeded', ),
                        status__in=('expired', 'draft', 'submitted', 'needs_work')
                    ):
                        activity.status = 'succeeded'
                        activity.save()

                    succeeded_contributions.update(status='failed')
                    failed_contributions.update(status='succeeded')
                    failed_contributions_new.update(status='new')
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
                    for registration in registrations_without_participant_multi_slot.all():
                        add_participant_to_registration(registration)

    if not fix and total_errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")

    if not total_errors:
        print("No errors found! 🎉🎉🎉")
