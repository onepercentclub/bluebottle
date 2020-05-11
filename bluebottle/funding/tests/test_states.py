from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(initiative=self.initiative)
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding.bank_account = bank_account
        self.funding.save()

    def test_approve(self):
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_reject(self):
        self.funding.states.reject(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.rejected.value)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def test_delete(self):
        self.funding.states.delete(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.deleted.value)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)
