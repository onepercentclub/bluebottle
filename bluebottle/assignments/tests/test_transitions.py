# -*- coding: utf-8 -*-
from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.activities.transitions import OrganizerTransitions
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.assignments.transitions import ApplicantTransitions
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.tests.factories import InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


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
        initiative = InitiativeFactory.create()
        assignment = AssignmentFactory.create(title='', initiative=initiative)

        self.assertEqual(assignment.status, 'submitted')

        organizer = assignment.contributions.get()
        self.assertEqual(organizer.status, OrganizerTransitions.values.new)
        self.assertEqual(organizer.user, assignment.owner)

    def test_default_status(self):
        self.assertEqual(
            self.assignment.status, 'open'
        )
        organizer = self.assignment.contributions.get()
        self.assertEqual(organizer.status, OrganizerTransitions.values.succeeded)
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
            applicant.status, ApplicantTransitions.values.closed
        )

    def test_start_no_applicants(self):
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, 'open'
        )

    def test_happy_life_cycle(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assertEqual(
            applicant.status, ApplicantTransitions.values.new
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
            applicant.status, ApplicantTransitions.values.active
        )

        self.assignment.states.succeed()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            self.assignment.status, 'succeeded'
        )
        self.assertEqual(
            applicant.status, ApplicantTransitions.values.succeeded
        )
        organizer = self.assignment.contributions.instance_of(Organizer).get()
        self.assertEqual(organizer.status, OrganizerTransitions.values.succeeded)

    def test_applied_should_succeed(self):
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assertEqual(
            applicant.status, ApplicantTransitions.values.new
        )
        self.assignment.states.start()
        self.assignment.states.succeed()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            applicant.status, ApplicantTransitions.values.succeeded
        )

    def test_time_spent_deadline(self):
        self.assignment.review_transitions.approve()
        self.assignment.save()
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assignment.states.start()
        self.assignment.states.succeed()
        self.assignment.save()
        applicant.refresh_from_db()
        self.assertEqual(
            applicant.time_spent, self.assignment.duration
        )

    def test_time_spent_on_date(self):
        self.assignment.end_date_type = 'on_date'
        self.assignment.preparation = 5
        self.assignment.review_transitions.approve()
        self.assignment.save()
        applicant = ApplicantFactory.create(activity=self.assignment)
        self.assignment.states.start()
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

        new_assignment.states.close()
        new_assignment.save()
        organizer.refresh_from_db()

        self.assertEqual(organizer.status, u'closed')

        new_assignment.states.reopen()
        new_assignment.save()
        organizer.refresh_from_db()

        self.assertEqual(organizer.status, u'succeeded')
