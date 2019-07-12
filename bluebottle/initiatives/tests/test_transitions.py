from django.core import mail

from bluebottle.fsm import TransitionNotPossible
from bluebottle.initiatives.transitions import InitiativeTransitions
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory


class InitiativeTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(InitiativeTransitionTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()

    def test_default_status(self):
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.draft
        )

    def test_submit(self):
        self.initiative.transitions.submit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_submit_incomplete(self):
        self.initiative.title = None

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_needs_work(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.needs_work()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.needs_work
        )

    def test_resubmit(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.needs_work()
        self.initiative.transitions.resubmit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_approve(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.approved
        )
        self.assertEqual(len(mail.outbox), 1)
        subject = 'Your initiative {} has been approved!'.format(self.initiative.title)
        self.assertEqual(mail.outbox[0].subject, subject)

    def test_close(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.close()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.closed
        )
        self.assertEqual(len(mail.outbox), 1)
        subject = 'Your initiative {} has been closed'.format(self.initiative.title)
        self.assertEqual(mail.outbox[0].subject, subject)

    def test_reopen(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.close()
        self.initiative.transitions.reopen()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )
