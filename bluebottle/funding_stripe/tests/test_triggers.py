from bluebottle.funding.messages import PayoutAccountRejected, LivePayoutAccountRejected
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory, ExternalAccountFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase
from bluebottle.funding.tests.factories import FundingFactory


class PayoutAccountTriggersTestCase(TriggerTestCase):

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)
        super().setUp()
        self.model = StripePayoutAccountFactory.create(status='verified')
        self.bank_account = ExternalAccountFactory.create(connect_account=self.model)
        self.funding = FundingFactory.create(
            status='draft',
            bank_account=self.bank_account
        )

    def test_reject_draft(self):
        self.model.states.reject()
        with self.execute():
            self.assertNotificationEffect(PayoutAccountRejected)
            self.assertNoNotificationEffect(LivePayoutAccountRejected)

    def test_reject_live(self):
        self.funding.status = 'open'
        self.funding.save()

        self.model.states.reject()
        with self.execute():
            self.assertNotificationEffect(PayoutAccountRejected)
            self.assertNotificationEffect(LivePayoutAccountRejected)
