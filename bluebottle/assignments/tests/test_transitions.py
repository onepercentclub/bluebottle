# -*- coding: utf-8 -*-
from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.transitions import ActivityReviewTransitions
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.assignments.transitions import AssignmentTransitions
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
        self.assignment.review_transitions.approve()
        self.assignment.transitions.start()
        self.assignment.save()

    def test_deadline_passed(self):
        self.assignment.transitions.expire()
        self.assignment.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your task Nice things has been closed')
        self.assertTrue('nobody applied to your task' in mail.outbox[0].body)

    def test_closed(self):
        self.assignment.transitions.close()
        self.assignment.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your task Nice things has been closed')
        self.assertTrue('has been closed by the platform admin' in mail.outbox[0].body)

    def test_succeed(self):
        self.assignment.transitions.succeed()
        self.assignment.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Your task Nice things has been completed! 🎉')
        self.assertTrue('Great news!' in mail.outbox[0].body)

    def test_applied(self):
        someone = BlueBottleUserFactory.create(first_name='Henk')
        ApplicantFactory.create(activity=self.assignment, user=someone)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'Someone applied to your task Nice things! 🙌')
        self.assertTrue('Henk applied to join your task' in mail.outbox[0].body)


class AssignmentTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(AssignmentTransitionTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        user = BlueBottleUserFactory.create()
        self.assignment = AssignmentFactory.create(
            end_date_type='deadline',
            end_date=(now() + timedelta(weeks=2)).date(),
            registration_deadline=(now() + timedelta(weeks=1)).date(),
            capacity=3,
            initiative=self.initiative,
            owner=user)

    def test_default_status(self):
        self.assertEqual(
            self.assignment.status, AssignmentTransitions.values.in_review
        )
        self.assertEqual(
            self.assignment.review_status, ActivityReviewTransitions.values.draft
        )

    def test_submit(self):
        self.assignment.review_transitions.submit()
        self.assertEqual(
            self.assignment.status, AssignmentTransitions.values.open
        )
        self.assertEqual(
            self.assignment.review_status, ActivityReviewTransitions.values.approved
        )

    def test_review(self):
        self.assignment.review_transitions.approve()
        self.assertEqual(
            self.assignment.status, AssignmentTransitions.values.open
        )
        self.assertEqual(
            self.assignment.review_status, ActivityReviewTransitions.values.approved
        )

    def test_close(self):
        self.assignment.review_transitions.approve()
        self.assignment.save()
        self.assignment.transitions.close()
        self.assignment.save()
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, AssignmentTransitions.values.closed
        )

    def test_start_no_applicants(self):
        self.assignment.review_transitions.approve()
        self.assignment.save()
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, AssignmentTransitions.values.open
        )

    def test_start(self):
        self.assignment.review_transitions.approve()
        self.assignment.save()
        ApplicantFactory.create(activity=self.assignment)
        ApplicantFactory.create(activity=self.assignment)
        self.assignment.transitions.start()
        self.assignment.save()
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, AssignmentTransitions.values.running
        )

    def test_full(self):
        self.assignment.review_transitions.approve()
        self.assignment.save()
        applicants = ApplicantFactory.create_batch(3, activity=self.assignment)
        for applicant in applicants:
            applicant.transitions.accept()
            applicant.save()
        assignment = Assignment.objects.get(pk=self.assignment.pk)
        self.assertEqual(
            assignment.status, AssignmentTransitions.values.full
        )
