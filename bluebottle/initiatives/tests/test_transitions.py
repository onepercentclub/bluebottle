from bluebottle.initiatives.models import Initiative
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory


class InitiativeTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(InitiativeTransitionTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()

    def test_default_status(self):
        self.assertEqual(
            self.initiative.status, Initiative.Status.draft
        )

    def test_submit(self):
        self.initiative.submit()
        self.assertEqual(
            self.initiative.status, Initiative.Status.submitted
        )

    def test_needs_work(self):
        self.initiative.submit()
        self.initiative.needs_work()
        self.assertEqual(
            self.initiative.status, Initiative.Status.needs_work
        )

    def test_resubmit(self):
        self.initiative.submit()
        self.initiative.needs_work()
        self.initiative.resubmit()
        self.assertEqual(
            self.initiative.status, Initiative.Status.submitted
        )

    def test_approve(self):
        self.initiative.submit()
        self.initiative.approve()
        self.assertEqual(
            self.initiative.status, Initiative.Status.approved
        )

    def test_close(self):
        self.initiative.submit()
        self.initiative.close()
        self.assertEqual(
            self.initiative.status, Initiative.Status.closed
        )

    def test_reopen(self):
        self.initiative.submit()
        self.initiative.close()
        self.initiative.reopen()
        self.assertEqual(
            self.initiative.status, Initiative.Status.submitted
        )
