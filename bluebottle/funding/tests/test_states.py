from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)

    def test_create(self):
        funding = FundingFactory.create(initiative=self.initiative)
        self.assertEqual(funding.status, FundingStateMachine.open.value)
        organizer = funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_reject(self):
        funding = FundingFactory.create(initiative=self.initiative)
        funding.states.reject(save=True)
        self.assertEqual(funding.status, FundingStateMachine.rejected.value)
        organizer = funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)
