from django.test.utils import override_settings

from bluebottle.funding.messages.funding.activity_manager import FundingPayoutAccountMarkedIncomplete, \
    FundingPayoutAccountVerified
from bluebottle.funding.messages.funding.platform_manager import LivePayoutAccountMarkedIncomplete
from bluebottle.funding.messages.grant_application.activity_manager import GrantApplicationPayoutAccountVerified, \
    GrantApplicationPayoutAccountMarkedIncomplete
from bluebottle.funding.tests.factories import FundingFactory, GrantApplicationFactory
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory, ExternalAccountFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase


@override_settings(
    SUPPORT_EMAIL_ADDRESSES=[
        'support@example.com',
    ]
)
class FundingPayoutAccountTriggersTestCase(TriggerTestCase):

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            email='staff@example.com',
            submitted_initiative_notifications=True
        )
        self.support_user = BlueBottleUserFactory.create(email='support@example.com')
        super().setUp()
        self.model = StripePayoutAccountFactory.create(
            status="verified", account_id="test-account-id"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=self.model)
        self.funding = FundingFactory.create(
            status='draft',
            bank_account=self.bank_account
        )

    def test_set_incomplete_draft(self):
        self.model.states.set_incomplete()
        with self.execute():
            self.assertNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)

    def test_disable_live(self):
        self.funding.status = 'open'
        self.funding.save()

        self.model.payments_enabled = False
        self.model.states.set_incomplete()

        with self.execute():
            self.assertNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNotificationEffect(
                LivePayoutAccountMarkedIncomplete,
                recipients=[self.staff_user, self.support_user]
            )


@override_settings(
    SUPPORT_EMAIL_ADDRESSES=[
        'support@example.com',
    ]
)
class GrantApplicationPayoutAccountTriggersTestCase(TriggerTestCase):

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            email='staff@example.com',
            submitted_initiative_notifications=True
        )
        self.support_user = BlueBottleUserFactory.create(email='support@example.com')
        super().setUp()
        self.model = StripePayoutAccountFactory.create(
            status="pending", account_id="test-account-id"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=self.model)
        self.grant_application = GrantApplicationFactory.create(
            status='open',
            bank_account=self.bank_account
        )

    def test_set_incomplete_draft(self):
        self.model.states.set_incomplete()
        with self.execute():
            self.assertNotificationEffect(GrantApplicationPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)

    def test_set_verified(self):
        self.model.states.verify()
        with self.execute():
            self.assertNotificationEffect(GrantApplicationPayoutAccountVerified)
            self.assertNoNotificationEffect(FundingPayoutAccountVerified)
            self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)
