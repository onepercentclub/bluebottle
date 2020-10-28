from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.tests.factories import InitiativePlatformSettingsFactory
from bluebottle.test.utils import BluebottleTestCase


class AssignmentStateMachineTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.initiative = InitiativeFactory()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            initiative=self.initiative
        )
        mail.outbox = []

    def test_initial(self):
        self.assertEqual(self.assignment.status, AssignmentStateMachine.draft.value)

        organizer = self.assignment.contributions.get()
        self.assertTrue(
            isinstance(organizer, Organizer)
        )
        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

    def test_incomplete(self):
        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            title='',
            initiative=self.initiative
        )

        self.assertEqual(self.assignment.status, AssignmentStateMachine.draft.value)

        organizer = self.assignment.contributions.get()
        self.assertTrue(
            isinstance(organizer, Organizer)
        )
        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)
        self.assertRaises(
            TransitionNotPossible,
            self.assignment.states.submit
        )

    def test_submit_initiative_not_submitted(self):
        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            initiative=InitiativeFactory.create()
        )

        self.assertEqual(self.assignment.status, AssignmentStateMachine.draft.value)

        self.assertRaises(
            TransitionNotPossible,
            self.assignment.states.submit
        )
        self.assignment.initiative.states.submit(save=True)
        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.submitted.value)

    def test_approve(self):
        self.assignment = AssignmentFactory.create(
            end_date_type='on_date',
            owner=self.initiative.owner,
            initiative=self.initiative,
            capacity=3
        )
        self.assignment.states.submit(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        organizer = self.assignment.contributions.get()
        self.assertTrue(
            isinstance(organizer, Organizer)
        )
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_close_end_date(self):
        self.assignment.states.submit(save=True)

        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.cancelled.value)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your task "{self.assignment.title}" has expired'
        )
        self.assertTrue('nobody applied to your task' in mail.outbox[0].body)

    def test_cancel(self):
        self.assignment.states.submit(save=True)
        self.assignment.states.cancel(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.cancelled.value)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your task "{self.assignment.title}" has been cancelled'
        )
        self.assertTrue(
            'Unfortunately your task “{}” has been cancelled.'.format(
                self.assignment.title
            )
            in mail.outbox[0].body
        )

    def test_reschedule_end_date(self):
        self.assignment.states.submit(save=True)
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assignment.registration_deadline = (now() + timedelta(days=1)).date()
        self.assignment.date = now() + timedelta(days=2)
        self.assignment.save()
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_reject(self):
        self.assignment.states.reject(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.assignment.status, AssignmentStateMachine.rejected.value)
        self.assertEqual(
            mail.outbox[0].subject,
            f'Your task "{self.assignment.title}" has been rejected'
        )
        self.assertTrue(
            'Unfortunately your task “{}” has been rejected.'.format(
                self.assignment.title
            )
            in mail.outbox[0].body
        )

    def test_restore(self):
        self.assignment.states.reject(save=True)
        self.assignment.states.restore(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.needs_work.value)

    def test_fill(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.full.value)

    def test_succeed(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.date = now() - timedelta(days=1)
        self.assignment.registration_date = now() - timedelta(days=1)
        self.assignment.save()

        for applicant in applicants:
            applicant.refresh_from_db()
            self.assertEqual(applicant.time_spent, self.assignment.duration)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.succeeded.value)
        self.assertEqual(
            mail.outbox[-1].subject,
            f'Your task "{self.assignment.title}" has been successfully completed! 🎉'
        )
        self.assertTrue('You did it!' in mail.outbox[-1].body)

    def test_succeed_then_reschedule(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assignment.date = now() + timedelta(days=1)
        self.assignment.save()

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_change_date(self):
        tomorrow = now() + timedelta(days=1)
        next_week = now() + timedelta(days=7)
        assignment = AssignmentFactory.create(
            capacity=5,
            end_date_type='on_date',
            date=tomorrow
        )
        applicants = ApplicantFactory.create_batch(
            3, activity=assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        mail.outbox = []
        assignment.date = next_week
        assignment.save()
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            mail.outbox[0].subject,
            f'The date of your task "{assignment.title}" has been changed.'
        )

    def test_change_deadline(self):
        tomorrow = now() + timedelta(days=1)
        next_week = now() + timedelta(days=7)
        assignment = AssignmentFactory.create(
            capacity=5,
            end_date_type='deadline',
            date=tomorrow
        )
        self.assignment.save()
        applicants = ApplicantFactory.create_batch(
            3, activity=assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)
        mail.outbox = []
        assignment.date = next_week
        assignment.save()
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(
            mail.outbox[0].subject,
            f'The deadline for your task "{assignment.title}" has been changed.'
        )

    def test_fill_capacity(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity - 1, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        self.assignment.capacity = self.assignment.capacity - 1
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.full.value)

    def test_unfill_reject(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        applicants[0].states.reject(save=True)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_unfill_delete(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        applicants[0].delete()

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_unfill_change_capacity(self):
        self.assignment.states.submit(save=True)
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.capacity += 1
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)


class ApplicantStateMachineTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.initiative = InitiativeFactory()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            initiative=self.initiative
        )
        self.assignment.states.submit(save=True)
        mail.outbox = []
        self.applicant = ApplicantFactory.create(activity=self.assignment)

    def test_initial(self):
        self.assertEqual(self.applicant.status, ApplicantStateMachine.new.value)

        self.assertTrue(
            self.assignment.followers.filter(user=self.applicant.user).exists()
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].recipients(),
            [self.assignment.owner.email]
        )

        self.assertEqual(
            mail.outbox[0].subject,
            f'Someone applied to your task "{self.assignment.title}"! 🙌'
        )

        self.assertTrue(
            f'{self.applicant.user.first_name} applied to '
            in mail.outbox[0].body
        )

    def test_withdraw(self):
        self.applicant.states.withdraw(save=True, user=self.applicant.user)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.withdrawn)
        self.assertFalse(
            self.assignment.followers.filter(user=self.applicant.user).exists()
        )

    def test_withdraw_owner(self):
        self.assertRaises(
            TransitionNotPossible,
            self.applicant.states.withdraw,
            save=True,
            user=self.assignment.owner
        )

    def test_accept(self):
        mail.outbox = []
        self.applicant.states.accept(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.accepted)

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].recipients(),
            [self.applicant.user.email]
        )

        self.assertEqual(
            mail.outbox[0].subject,
            'You have been accepted for the task "{}"!'.format(
                self.assignment.title
            )
        )

    def test_reapply(self):
        self.applicant.states.withdraw(save=True, user=self.applicant.user)
        mail.outbox = []
        self.applicant.states.reapply(save=True, user=self.applicant.user)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.new)

        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(
            mail.outbox[0].recipients(),
            [self.assignment.owner.email]
        )

        self.assertEqual(
            mail.outbox[0].subject,
            f'Someone applied to your task "{self.assignment.title}"! 🙌'
        )

        self.assertTrue(
            f'{self.applicant.user.first_name} applied to '
            in mail.outbox[0].body
        )

    def test_accept_fill(self):
        self.assignment.capacity = 1
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.accepted)
        self.assignment.refresh_from_db()

        self.assertTrue(self.assignment.status, AssignmentStateMachine.full)

    def test_accept_then_withdraw(self):
        self.assignment.capacity = 1
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)
        self.applicant.states.withdraw(save=True, user=self.applicant.user)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.withdrawn)
        self.assignment.refresh_from_db()

        self.assertTrue(self.assignment.status, AssignmentStateMachine.open)

    def test_accept_then_reject(self):
        self.assignment.capacity = 1
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)
        self.applicant.states.reject(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.rejected)
        self.assignment.refresh_from_db()

        self.assertTrue(self.assignment.status, AssignmentStateMachine.open)

    def test_accept_succeed(self):
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.succeeded)
        self.assignment.refresh_from_db()

        self.assertTrue(self.assignment.status, AssignmentStateMachine.succeeded)

        self.assertTrue(self.applicant.time_spent, self.assignment.duration)

    def test_accept_set_time_spent(self):
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.succeeded)

        self.applicant.time_spent = 0
        self.applicant.save()

        self.assertTrue(self.applicant.status, ApplicantStateMachine.no_show)

    def test_accept_succeed_deadline(self):
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.preparation = 10
        self.assignment.end_date_type = 'on_date'
        self.assignment.save()

        self.applicant.states.accept(save=True, user=self.assignment.owner)

        self.assertTrue(self.applicant.status, ApplicantStateMachine.succeeded)
        self.assignment.refresh_from_db()

        self.assertTrue(self.assignment.status, AssignmentStateMachine.succeeded)

        self.assertTrue(
            self.applicant.time_spent,
            self.assignment.duration + self.assignment.preparation
        )

    def test_accept_user(self):
        self.assertRaises(
            TransitionNotPossible,
            self.applicant.states.accept,
            save=True,
            user=self.applicant.user
        )
