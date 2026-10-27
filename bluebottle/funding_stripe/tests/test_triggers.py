from django.contrib.auth.models import Group
from django.test.utils import override_settings

from bluebottle.funding.messages.funding.activity_manager import (
    FundingPayoutAccountMarkedIncomplete,
    FundingPublicPayoutAccountMarkedIncomplete,
)
from bluebottle.funding.messages.funding.platform_manager import (
    LivePayoutAccountMarkedIncomplete,
    LivePublicPayoutAccountMarkedIncomplete,
)
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.funding_stripe.tests.base import FundingStripeMixin, save_stripe_payout_account
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory, ExternalAccountFactory
from bluebottle.grant_management.messages.activity_manager import GrantApplicationPayoutAccountMarkedIncomplete
from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase


DRAFT_FUNDING_STATUSES = [
    'draft',
    'needs_work',
    'submitted',
]

ACTIVE_FUNDING_STATUSES = [
    'open',
    'on_hold',
]

INACTIVE_FUNDING_STATUSES = [
    'rejected',
    'succeeded',
    'partially_funded',
    'cancelled',
    'refunded',
]

INACTIVE_GRANT_APPLICATION_STATUSES = [
    'draft',
    'needs_work',
    'rejected',
    'submitted',
    'open',
    'succeeded',
    'cancelled',
]


@override_settings(
    SUPPORT_EMAIL_ADDRESSES=[
        'support@example.com',
    ]
)
class FundingPayoutAccountTriggersTestCase(FundingStripeMixin, TriggerTestCase):

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            email='staff@example.com',
            submitted_initiative_notifications=True
        )
        self.staff_user.groups.add(Group.objects.get(name='Staff'))
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

    def trigger_set_incomplete(self):
        self.model.status = 'verified'
        save_stripe_payout_account(self.model)
        self.model.states.set_incomplete()

    def test_set_incomplete_draft_funding_sends_activity_manager_notification(self):
        for status in DRAFT_FUNDING_STATUSES:
            with self.subTest(status=status):
                self.funding.status = status
                self.funding.save()
                self.trigger_set_incomplete()
                with self.execute():
                    self.assertNotificationEffect(FundingPayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(LivePublicPayoutAccountMarkedIncomplete)

    def test_set_incomplete_active_funding_sends_platform_manager_notification(self):
        for status in ACTIVE_FUNDING_STATUSES:
            with self.subTest(status=status):
                self.funding.status = status
                self.funding.save()
                self.trigger_set_incomplete()
                with self.execute():
                    self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
                    self.assertNotificationEffect(
                        LivePayoutAccountMarkedIncomplete,
                        recipients=[self.staff_user]
                    )

    def test_set_incomplete_draft_vs_open_send_different_notifications(self):
        self.trigger_set_incomplete()
        with self.execute():
            self.assertNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)

        self.funding.status = 'open'
        self.funding.save()
        self.trigger_set_incomplete()
        with self.execute():
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNotificationEffect(
                LivePayoutAccountMarkedIncomplete,
                recipients=[self.staff_user]
            )

    def test_set_incomplete_inactive_funding_statuses_send_no_notification(self):
        for status in INACTIVE_FUNDING_STATUSES:
            with self.subTest(status=status):
                self.funding.status = status
                self.funding.save()
                self.trigger_set_incomplete()
                with self.execute():
                    self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(FundingPublicPayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(LivePayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(LivePublicPayoutAccountMarkedIncomplete)

    def test_set_incomplete_public_draft_sends_public_activity_manager_notification(self):
        self.model.public = True
        save_stripe_payout_account(self.model)
        self.trigger_set_incomplete()
        with self.execute():
            self.assertNotificationEffect(FundingPublicPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(LivePublicPayoutAccountMarkedIncomplete)

    def test_set_incomplete_public_open_sends_public_platform_manager_notification(self):
        self.model.public = True
        save_stripe_payout_account(self.model)
        self.funding.status = 'open'
        self.funding.save()
        self.trigger_set_incomplete()
        with self.execute():
            self.assertNotificationEffect(LivePublicPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(FundingPublicPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)

    def test_disable_live(self):
        self.funding.status = 'open'
        self.funding.save()

        self.model.payments_enabled = False
        self.model.states.set_incomplete()

        with self.execute():
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
            self.assertNotificationEffect(
                LivePayoutAccountMarkedIncomplete,
                recipients=[self.staff_user]
            )


@override_settings(
    SUPPORT_EMAIL_ADDRESSES=[
        'support@example.com',
    ]
)
class GrantApplicationPayoutAccountIncompleteTriggersTestCase(FundingStripeMixin, TriggerTestCase):

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        super().setUp()
        self.model = StripePayoutAccountFactory.create(
            status="pending", account_id="test-account-id"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=self.model)
        self.grant_application = GrantApplicationFactory.create(
            status='draft',
            bank_account=self.bank_account
        )

    def _trigger_set_incomplete(self):
        self.model.status = 'verified'
        save_stripe_payout_account(self.model)
        self.model.states.set_incomplete()

    def test_set_incomplete_inactive_grant_application_statuses(self):
        for status in INACTIVE_GRANT_APPLICATION_STATUSES:
            with self.subTest(status=status):
                self.grant_application.status = status
                self.grant_application.save()
                self._trigger_set_incomplete()
                with self.execute():
                    self.assertNoNotificationEffect(GrantApplicationPayoutAccountMarkedIncomplete)
                    self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)

    def test_set_incomplete_granted_sends_notification(self):
        self.grant_application.status = 'granted'
        self.grant_application.save()
        self._trigger_set_incomplete()
        with self.execute():
            self.assertNotificationEffect(GrantApplicationPayoutAccountMarkedIncomplete)
            self.assertNoNotificationEffect(FundingPayoutAccountMarkedIncomplete)
