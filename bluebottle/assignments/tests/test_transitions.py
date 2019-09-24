# -*- coding: utf-8 -*-
from django.core import mail

from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
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
        self.assertEqual(mail.outbox[0].subject, 'Your task Nice things has been completed!')
        self.assertTrue('Great news!' in mail.outbox[0].body)

    def test_applied(self):
        someone = BlueBottleUserFactory.create(first_name='Henk')
        ApplicantFactory.create(activity=self.assignment, user=someone, status='draft')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Someone applied to your task!')
        self.assertTrue('Henk applied to join your task' in mail.outbox[0].body)
