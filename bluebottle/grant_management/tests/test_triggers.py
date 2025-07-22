from django.core import mail
from moneyed import Money

from bluebottle.activities.messages.activity_manager import (
    ActivityRejectedNotification, ActivitySubmittedNotification,
    ActivityApprovedNotification, ActivityNeedsWorkNotification
)
from bluebottle.activities.messages.reviewer import ActivitySubmittedReviewerNotification
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.grant_management.messages.activity_manager import (
    GrantApplicationPayoutAccountMarkedIncomplete,
    GrantApplicationPayoutAccountVerified,
    GrantApplicationSubmittedMessage,
    GrantApplicationApprovedMessage,
    GrantApplicationNeedsWorkMessage,
    GrantApplicationRejectedMessage,
    GrantApplicationCancelledMessage
)
from bluebottle.grant_management.models import GrantPayment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase

from django.test.utils import override_settings

import mock
import munch
import stripe

from bluebottle.funding.messages.funding.activity_manager import (
    FundingPayoutAccountMarkedIncomplete,
    FundingPayoutAccountVerified
)

from bluebottle.grant_management.tests.factories import (
    GrantApplicationFactory,
    GrantDepositFactory,
    GrantFundFactory,
    GrantDonorFactory,
    GrantPaymentFactory, GrantProviderFactory, GrantPayoutFactory
)
from bluebottle.funding_stripe.tests.factories import (
    StripePayoutAccountFactory,
    ExternalAccountFactory
)

from bluebottle.funding.messages.funding.platform_manager import LivePayoutAccountMarkedIncomplete


COUNTRY_SPEC = stripe.CountrySpec('NL')
COUNTRY_SPEC.update(
    {
        "supported_bank_account_currencies": ['EUR'],
        "verification_fields": munch.munchify(
            {
                "individual": munch.munchify(
                    {
                        "additional": ["individual.verification.document"],
                        "minimum": ["individual.first_name"],
                    }
                )
            }
        )
    }
)


class GrantApplicationTriggersTestCase(TriggerTestCase):
    factory = GrantApplicationFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

        image = ImageFactory()

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'target': Money(1000, 'EUR'),
            'image': image,
        }
        super().setUp()

    def create(self):
        self.model = self.factory.create(**self.defaults)

    def test_submit(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationSubmittedMessage)
            self.assertNoNotificationEffect(ActivitySubmittedReviewerNotification)
            self.assertNoNotificationEffect(ActivitySubmittedNotification)

    def test_approve(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationApprovedMessage)
            self.assertNoNotificationEffect(ActivityApprovedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)

    def test_needs_work(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.request_changes()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationNeedsWorkMessage)
            self.assertNoNotificationEffect(ActivityNeedsWorkNotification)

    def test_reject(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.reject()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationRejectedMessage)
            self.assertNoNotificationEffect(ActivityRejectedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)

    def test_cancel(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.cancel()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationCancelledMessage)
            self.assertNoNotificationEffect(ActivityRejectedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)


class GrantDepositTriggerTestCase(TriggerTestCase):
    factory = GrantDepositFactory

    def setUp(self):
        self.fund = GrantFundFactory.create()
        self.defaults = {
            'fund': self.fund,
            'amount': Money(1000, 'EUR')
        }
        self.create()

    def test_initial(self):
        self.model.ledger_item.refresh_from_db()

        self.assertEqual(self.model.status, 'final')
        self.assertEqual(self.model.ledger_item.status, 'final')
        self.assertEqual(self.fund.balance, Money(1000, 'EUR'))

    def test_cancel(self):
        self.model.states.cancel(save=True)

        self.model.ledger_item.refresh_from_db()

        self.assertEqual(self.model.status, 'cancelled')
        self.assertEqual(self.model.ledger_item.status, 'removed')
        self.assertEqual(self.fund.balance, Money(0, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(0, 'EUR'))


class GrantDonorTriggerTestCase(TriggerTestCase):
    factory = GrantDonorFactory

    def setUp(self):
        self.fund = GrantFundFactory.create()

        GrantDepositFactory.create(
            fund=self.fund,
            amount=Money(1500, 'EUR')
        )
        self.application = GrantApplicationFactory.create(
            status='submitted',
            initiative=None,
            target=Money(500, 'EUR')
        )
        self.defaults = {
            'activity': self.application,
            'amount': Money(500, 'EUR'),
            'fund': self.fund,
            'payout': None
        }
        self.application.states.approve(save=True)

    def test_initial(self):
        self.create()
        self.assertEqual(self.model.status, 'new')
        self.assertEqual(self.application.status, 'granted')

        self.assertEqual(self.model.ledger_item.status, 'pending')

        self.assertEqual(self.fund.balance, Money(1500, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(500, 'EUR'))

    def get_bank_account(self):
        with mock.patch(
            "stripe.CountrySpec.retrieve", return_value=COUNTRY_SPEC
        ):
            payout_account = StripePayoutAccountFactory.create(
                status="pending", account_id="test-account-id"
            )
            return ExternalAccountFactory.create(
                connect_account=payout_account
            )

    def test_paid(self):
        self.create()

        self.application.bank_account = self.get_bank_account()
        self.application.save()

        self.assertIsNone(self.application.payouts.first())

        self.application.bank_account.connect_account.states.verify(save=True)

        payout = self.application.payouts.get()
        self.assertEqual(payout.status, 'new')

        self.assertEqual(self.fund.balance, Money(1500, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(500, 'EUR'))

    def test_paid_existing_payout_account(self):
        bank_account = self.get_bank_account()
        bank_account.connect_account.states.verify(save=True)

        self.create()

        self.application.bank_account = bank_account
        self.application.save()

        payout = self.application.payouts.get()
        self.assertEqual(payout.status, 'new')

        self.assertEqual(self.fund.balance, Money(1500, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(500, 'EUR'))


class GrantPaymentTriggerTestCase(TriggerTestCase):
    factory = GrantPaymentFactory

    def setUp(self):
        self.fund = GrantFundFactory.create()
        self.deposit = GrantDepositFactory.create(
            fund=self.fund,
            amount=Money(1000, 'EUR')
        )
        self.application = GrantApplicationFactory.create(
            initiative=None,
            status='submitted'
        )

        self.donor = GrantDonorFactory.create(
            activity=self.application,
            fund=self.fund,
            amount=Money(1000, 'EUR'),
            payout=None
        )

        with mock.patch(
            "stripe.CountrySpec.retrieve", return_value=COUNTRY_SPEC
        ):
            payout_account = StripePayoutAccountFactory.create(
                status="pending",
                account_id="test-account-id"
            )
            self.application.bank_account = ExternalAccountFactory.create(
                connect_account=payout_account
            )
            payout_account.states.verify(save=True)

            self.application.save()

        self.payout = self.application.payouts.get()
        self.defaults = {}
        self.create()

    def create(self):
        super().create()

        self.payout.payment = self.model
        self.payout.save()

    def test_initial(self):
        self.assertEqual(self.model.status, 'new')
        self.assertEqual(self.donor.status, 'new')
        self.assertEqual(self.application.status, 'granted')

        self.assertEqual(self.donor.ledger_item.status, 'pending')

        self.assertEqual(self.fund.balance, Money(1000, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(1000, 'EUR'))

    def test_succeed(self):
        with mock.patch(
            "stripe.Transfer.create"
        ) as create_transfer:
            self.model.states.succeed(save=True)

        create_transfer.assert_called_with(
            amount=100000,
            currency='eur',
            destination='test-account-id',
            description=f'Grant payout for {self.application.title}',
            metadata={
                'payout_id': str(self.payout.pk),
                'grant_application_id': str(self.application.pk),
                'grant_application_title': self.application.title
            }
        )

        self.assertEqual(self.model.status, 'succeeded')
        self.donor.refresh_from_db()

        self.assertEqual(self.donor.status, 'succeeded')

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'granted')

        self.donor.ledger_item.refresh_from_db()
        self.assertEqual(self.donor.ledger_item.status, 'final')

        self.assertEqual(self.fund.balance, Money(0, 'EUR'))
        self.assertEqual(self.fund.total_pending, Money(0, 'EUR'))


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


class GrantPaymentTriggersTestCase(TriggerTestCase):
    def setUp(self):
        finance_manager = BlueBottleUserFactory.create()
        self.provider = GrantProviderFactory.create(
            name="Test Provider",
            owner=finance_manager
        )
        fund = GrantFundFactory.create(
            name="Test Fund",
            grant_provider=self.provider
        )

        grant_application1 = GrantApplicationFactory.create(
            title="Save the world!",
            status='granted'
        )
        payout1 = GrantPayoutFactory.create(
            activity=grant_application1,
            status='approved',
        )
        GrantDonorFactory.create(
            payout=payout1,
            activity=grant_application1,
            fund=fund,
            amount=Money(2000, 'EUR')
        )

        grant_application2 = GrantApplicationFactory.create(
            title="Save the world!",
            status='granted'
        )
        payout2 = GrantPayoutFactory.create(
            activity=grant_application2,
            status='approved'
        )

        GrantDonorFactory.create(
            payout=payout2,
            activity=grant_application2,
            fund=fund,
            amount=Money(1500, 'EUR')
        )

    def test_create(self):
        mail.outbox = []
        self.provider.create_payment()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'A grant payment request is ready on Test'
        )
        payment = GrantPayment.objects.first()
        self.assertEqual(payment.status, 'pending')
