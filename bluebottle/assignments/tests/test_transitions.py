# -*- coding: utf-8 -*-
from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.tests.factories import InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
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

    def test_accept(self):
        self.assignment.states.reject(save=True)
        self.assignment.states.accept(save=True)

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

    def test_accept_user(self):
        self.assertRaises(
            TransitionNotPossible,
            self.applicant.states.accept,
            save=True,
            user=self.applicant.user
        )


class AssignmentTransitionMessagesTestCase(BluebottleTestCase):
    def setUp(self):
        super(AssignmentTransitionMessagesTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['assignment']
        )
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.assignment = AssignmentFactory.create(
            owner=self.user,
            title='Nice things',
            initiative=self.initiative
        )
        self.initiative.states.approve(save=True)
        self.assignment.refresh_from_db()
        self.assignment.states.start(save=True)
        mail.outbox = []

    def test_deadline_passed(self):
        self.assignment.states.expire(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your task "Nice things" has been closed')
        self.assertTrue('nobody applied to your task' in mail.outbox[0].body)

    def test_closed(self):
        self.assignment.states.close(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your task "Nice things" has been closed')
        self.assertTrue('has been closed by the platform admin' in mail.outbox[0].body)

    def test_succeed(self):
        self.assignment.states.succeed(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Your task "Nice things" has been completed! 🎉')
        self.assertTrue('Great news!' in mail.outbox[0].body)

    def test_applied(self):
        someone = BlueBottleUserFactory.create(first_name='Henk')
        ApplicantFactory.create(activity=self.assignment, user=someone)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Someone applied to your task "Nice things"! 🙌')
        self.assertTrue('Henk applied to join your task' in mail.outbox[0].body)


class AssignmentTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(AssignmentTransitionTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)

        user = BlueBottleUserFactory.create()
        self.assignment = AssignmentFactory.create(
            end_date_type='deadline',
            date=now() + timedelta(weeks=2),
            registration_deadline=(now() + timedelta(weeks=1)).date(),
            capacity=3,
            initiative=self.initiative,
            owner=user,
            duration=10,
        )

    def test_new(self):
        assignment = AssignmentFactory.create(title='', initiative=self.initiative)
        assignment.states.submit(save=True)
        self.assertEqual(assignment.status, 'submitted')
        organizer = assignment.contributions.get()
        self.assertEqual(organizer.status, 'new')
        self.assertEqual(organizer.user, assignment.owner)

    def test_default_status(self):
        self.assertEqual(
            self.assignment.status, 'open'
        )
        organizer = self.assignment.contributions.get()
        self.assertEqual(organizer.status, 'succeeded')
        self.assertEqual(organizer.user, self.assignment.owner)

    def test_close(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        applicant.states.accept()
        applicant.save()

        self.assignment.save()
        self.assignment.states.close()
        self.assignment.save()

        self.assignment.refresh_from_db()
        applicant.refresh_from_db()

        self.assertEqual(
            self.assignment.status, 'closed'
        )
        self.assertEqual(
            applicant.status, 'closed'
        )

    def test_start_no_applicants(self):
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, 'open'
        )

    def test_happy_life_cycle(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assertEqual(
            applicant.status, 'new'
        )
        applicant.states.accept()
        applicant.save()

        self.assignment.states.start()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            self.assignment.status, 'running'
        )
        self.assertEqual(
            applicant.status, 'active'
        )

        self.assignment.states.succeed()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            self.assignment.status, 'succeeded'
        )
        self.assertEqual(
            applicant.status, 'succeeded'
        )
        organizer = self.assignment.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_applied_should_succeed(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assertEqual(
            applicant.status, 'new'
        )
        applicant.states.accept(save=True)
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)
        applicant.refresh_from_db()
        self.assertEqual(
            applicant.status, 'succeeded'
        )

    def test_time_spent_deadline(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        applicant.states.accept()
        self.assignment.states.start(save=True)
        self.assignment.states.succeed(save=True)
        applicant.refresh_from_db()
        self.assertEqual(
            applicant.time_spent, self.assignment.duration
        )

    def test_time_spent_on_date(self):
        self.assignment.end_date_type = 'on_date'
        self.assignment.preparation = 5
        self.assignment.states.approve(save=True)
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assignment.states.succeed()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            applicant.time_spent, self.assignment.duration + self.assignment.preparation
        )

    def test_full(self):
        applicants = ApplicantFactory.create_batch(3, activity=self.assignment)
        for applicant in applicants:
            applicant.states.accept()
            applicant.save()
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, 'full'
        )
        # After withdrawal it should open again
        applicants[0].states.withdraw()
        applicants[0].save()
        assignment.refresh_from_db()
        self.assertEqual(
            assignment.status, 'open'
        )

    def test_new_assignment_for_running_initiative(self):
        new_assignment = AssignmentFactory.create(
            initiative=self.initiative,
            capacity=1
        )
        organizer = new_assignment.contributions.first()

        self.assertEqual(organizer.status, u'succeeded')

        new_assignment.states.close(save=True)
        organizer.refresh_from_db()

        self.assertEqual(organizer.status, u'closed')

        new_assignment.states.restore(save=True)
        organizer.refresh_from_db()

        self.assertEqual(organizer.status, u'succeeded')
