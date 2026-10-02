"""
Characterization tests for scripts/incorrect_contributions.py.

These tests pin down the *current* behaviour of the script, including
behaviour that is known to be wrong, so it can be refactored safely.
Tests that document a known bug say so in their docstring; when fixing the
bug, update the assertion in that test.

The script bypasses the FSM and uses queryset updates, so the inconsistent
states below are created the same way: through `.update()` calls.
"""
import io
from contextlib import redirect_stdout
from datetime import timedelta

from django.utils.timezone import now

from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import TimeContribution
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleRegistrationFactory,
)
from scripts.incorrect_contributions import run


class IncorrectContributionsScriptTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(
            activity_types=[
                'dateactivity', 'deadlineactivity', 'periodicactivity', 'scheduleactivity'
            ]
        )
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

    def run_script(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            run(*args)
        return output.getvalue()

    def force_status(self, obj, status):
        type(obj).objects.filter(pk=obj.pk).update(status=status)

    def create_activity(self, factory):
        activity = factory.create(
            initiative=self.initiative,
            review=False,
            registration_deadline=None,
        )
        activity.states.publish(save=True)
        return activity

    def register(self, activity, registration_factory):
        user = BlueBottleUserFactory.create()
        registration = registration_factory.create(activity=activity, user=user, as_user=user)
        return registration.participants.get()

    def create_date_participant(self, activity=None):
        activity = activity or self.create_activity(DateActivityFactory)
        user = BlueBottleUserFactory.create()
        registration = DateRegistrationFactory.create(activity=activity, user=user, as_user=user)
        return DateParticipantFactory.create(
            registration=registration, slot=activity.slots.get()
        )

    def contribution(self, participant):
        return TimeContribution.objects.get(contributor=participant)

    def move_date_activity_to_past(self, activity):
        """Put the activity, its slot and contributions in the past, as if it has happened."""
        past = now() - timedelta(days=7)
        slot = activity.slots.get()
        type(slot).objects.filter(pk=slot.pk).update(start=past, status='finished')
        self.force_status(activity, 'succeeded')
        TimeContribution.objects.filter(contributor__activity=activity).update(
            start=past, end=past + slot.duration
        )

    # Baseline / reporting

    def test_consistent_data_reports_no_errors(self):
        participant = self.create_date_participant()
        self.assertStatus(self.contribution(participant), 'new')

        output = self.run_script('fix')

        self.assertIn('No errors found!', output)
        self.assertStatus(self.contribution(participant), 'new')

    def test_without_fix_reports_but_does_not_change(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.force_status(contribution, 'failed')

        output = self.run_script()

        self.assertIn('### Tenant Test:', output)
        self.assertIn('failed or new but should be succeeded: 1', output)
        self.assertIn("Add '--script-args=fix'", output)
        self.assertStatus(contribution, 'failed')

    def test_verbose_lists_contribution_ids(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.force_status(contribution, 'failed')

        output = self.run_script('verbose')

        self.assertIn(f'IDs: {contribution.pk}', output)

    # Date activities

    def test_date_failed_contribution_with_future_slot_is_set_to_succeeded(self):
        """
        Known bug (BB-30168): the slot is still in the future, so the contribution
        should become 'new', not 'succeeded'.
        """
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.assertTrue(contribution.start > now())
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    def test_date_failed_contribution_with_past_slot_is_set_to_succeeded(self):
        participant = self.create_date_participant()
        self.move_date_activity_to_past(participant.activity)
        contribution = self.contribution(participant)
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    def test_date_new_contribution_succeeded_activity_is_not_fixed_on_its_own(self):
        """
        Known bug: 'new but should be succeeded' is not part of the error check,
        so when it is the only problem nothing gets reported or fixed.
        """
        participant = self.create_date_participant()
        self.move_date_activity_to_past(participant.activity)
        contribution = self.contribution(participant)
        self.assertStatus(contribution, 'new')

        output = self.run_script('fix')

        self.assertIn('No errors found!', output)
        self.assertStatus(contribution, 'new')

    def test_date_new_contribution_succeeded_activity_is_fixed_with_other_errors(self):
        participant = self.create_date_participant()
        self.move_date_activity_to_past(participant.activity)
        contribution = self.contribution(participant)

        # An unrelated error on the same tenant makes the fix block run
        other = self.create_date_participant()
        self.force_status(self.contribution(other), 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    def test_date_succeeded_contribution_withdrawn_participant_is_set_to_failed(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.force_status(participant, 'withdrawn')
        self.force_status(contribution, 'succeeded')

        self.run_script('fix')

        self.assertStatus(contribution, 'failed')

    def test_date_new_contribution_withdrawn_participant_is_set_to_failed(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.force_status(participant, 'withdrawn')

        self.run_script('fix')

        self.assertStatus(contribution, 'failed')

    def test_date_failed_contribution_withdrawn_participant_stays_failed(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        participant.states.withdraw(save=True)
        self.assertStatus(contribution, 'failed')

        output = self.run_script('fix')

        self.assertIn('No errors found!', output)
        self.assertStatus(contribution, 'failed')

    def test_date_failed_contribution_rejected_registration_stays_failed(self):
        participant = self.create_date_participant()
        contribution = self.contribution(participant)
        self.force_status(participant.registration, 'rejected')
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'failed')

    # Deadline activities

    def test_deadline_failed_contribution_open_activity_is_set_to_succeeded(self):
        """
        Deadline participants succeed as soon as they are accepted (FSM behaviour),
        so this matches what the FSM would do.
        """
        participant = self.register(
            self.create_activity(DeadlineActivityFactory), DeadlineRegistrationFactory
        )
        contribution = self.contribution(participant)
        self.assertStatus(participant, 'succeeded')
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    def test_deadline_stopped_participants_are_set_to_succeeded(self):
        participant = self.register(
            self.create_activity(DeadlineActivityFactory), DeadlineRegistrationFactory
        )
        self.force_status(participant, 'stopped')

        # Stopped participants are not reported as an error themselves, so an
        # unrelated error on the same tenant is needed to make the fix block run
        other = self.create_date_participant()
        self.force_status(self.contribution(other), 'failed')

        self.run_script('fix')

        self.assertStatus(participant, 'succeeded')

    # Schedule activities

    def test_schedule_failed_contribution_unscheduled_slot_is_set_to_succeeded(self):
        """
        Known bug (BB-30168): the participant has not been scheduled yet,
        so the contribution should become 'new', not 'succeeded'.
        """
        participant = self.register(
            self.create_activity(ScheduleActivityFactory), ScheduleRegistrationFactory
        )
        self.assertStatus(participant, 'accepted')
        contribution = self.contribution(participant)
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    # Periodic activities

    def test_periodic_failed_contribution_open_activity_is_set_to_succeeded(self):
        """
        Known bug (BB-30168): the script does not look at the slot at all.
        """
        participant = self.register(
            self.create_activity(PeriodicActivityFactory), PeriodicRegistrationFactory
        )
        self.force_status(participant, 'accepted')
        contribution = self.contribution(participant)
        self.force_status(contribution, 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'succeeded')

    def test_periodic_new_contribution_finished_slot_is_not_set_to_succeeded(self):
        """
        Known bug: the query uses `slot__status__in=('finished')`, which is a
        string instead of a tuple, so it never matches a finished slot.
        """
        participant = self.register(
            self.create_activity(PeriodicActivityFactory), PeriodicRegistrationFactory
        )
        self.force_status(participant, 'accepted')
        self.force_status(participant.slot, 'finished')
        contribution = self.contribution(participant)
        self.assertStatus(contribution, 'new')

        # An unrelated error on the same tenant makes the fix block run
        other = self.create_date_participant()
        self.force_status(self.contribution(other), 'failed')

        self.run_script('fix')

        self.assertStatus(contribution, 'new')
