# -*- coding: utf-8 -*-
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
        super(AssignmentStateMachineTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.initiative = InitiativeFactory()
        self.initiative.states.approve(save=True)

        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            initiative=self.initiative
        )
        mail.outbox = []

    def test_initial(self):
        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        organizer = self.assignment.contributions.get()
        self.assertTrue(
            isinstance(organizer, Organizer)
        )
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

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

    def test_approve(self):
        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            title='',
            initiative=self.initiative
        )
        self.assignment.title = 'Some title'
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        organizer = self.assignment.contributions.get()
        self.assertTrue(
            isinstance(organizer, Organizer)
        )
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_close_end_date(self):
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.closed.value)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'Your task "{}" has been closed'.format(self.assignment.title)
        )
        self.assertTrue('nobody applied to your task' in mail.outbox[0].body)

    def test_reopen_end_date(self):
        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assignment.date = now() + timedelta(days=1)
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_reject(self):
        self.assignment.states.reject(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.rejected.value)

    def test_restore(self):
        self.assignment.states.reject(save=True)
        self.assignment.states.restore(save=True)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_fill(self):
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.full.value)

    def test_succeed(self):
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        for applicant in applicants:
            applicant.refresh_from_db()
            self.assertEqual(applicant.time_spent, self.assignment.duration)

        self.assertEqual(self.assignment.status, AssignmentStateMachine.succeeded.value)
        self.assertEqual(
            mail.outbox[-1].subject,
            u'Your task "{}" has been completed! 🎉'.format(self.assignment.title)
        )
        self.assertTrue('Great news!' in mail.outbox[-1].body)

    def test_succeed_then_reopen(self):
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        self.assignment.date = now() - timedelta(days=1)
        self.assignment.save()

        self.assignment.date = now() + timedelta(days=1)
        self.assignment.save()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_fill_capacity(self):
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
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        applicants[0].states.reject(save=True)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_unfill_delete(self):
        applicants = ApplicantFactory.create_batch(
            self.assignment.capacity, activity=self.assignment
        )
        for applicant in applicants:
            applicant.states.accept(save=True)

        applicants[0].delete()

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.status, AssignmentStateMachine.open.value)

    def test_unfill_change_capacity(self):
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
        super(ApplicantStateMachineTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.initiative = InitiativeFactory()
        self.initiative.states.approve(save=True)

        self.assignment = AssignmentFactory.create(
            owner=self.initiative.owner,
            initiative=self.initiative
        )
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
            u'Someone applied to your task "{}"! 🙌'.format(self.assignment.title)
        )

        self.assertTrue(
            '{} applied to join'.format(self.applicant.user.first_name)
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
            u'You have been accepted for the task "{}"!'.format(
                self.assignment.title
            )
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
