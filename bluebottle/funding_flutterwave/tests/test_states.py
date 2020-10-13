from bluebottle.files.tests.factories import PrivateDocumentFactory
from bluebottle.funding.tests.factories import (
    FundingFactory, PlainPayoutAccountFactory, BudgetLineFactory
)
from bluebottle.funding_flutterwave.tests.factories import FlutterwaveBankAccountFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.initiatives.tests.factories import InitiativeFactory


class FlutterwavePayoutAccountTestCase(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create(status='approved')
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.document = PrivateDocumentFactory.create()
        self.payout_account = PlainPayoutAccountFactory.create(document=self.document)
        self.bank_account = FlutterwaveBankAccountFactory.create(connect_account=self.payout_account)
        self.funding.bank_account = self.bank_account
        self.funding.save()
        BudgetLineFactory.create(activity=self.funding)

    def test_approve_bank_account(self):
        self.bank_account.states.verify(save=True)
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.status, 'verified')
        self.payout_account.refresh_from_db()
        self.assertEqual(self.payout_account.status, 'verified')
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'submitted')
