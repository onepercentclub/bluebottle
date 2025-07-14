from datetime import timedelta
from unittest import mock

import stripe
from django.utils.timezone import now
from djmoney.money import Money

from bluebottle.activities.messages.activity_manager import (
    ActivityRejectedNotification, ActivitySubmittedNotification,
    ActivityApprovedNotification, ActivityNeedsWorkNotification
)
from bluebottle.activities.messages.reviewer import ActivitySubmittedReviewerNotification
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.messages.activity_manager import (
    FundingSubmittedMessage, FundingApprovedMessage, FundingNeedsWorkMessage,
    FundingRejectedMessage
)
from bluebottle.funding.messages.reviewer import FundingSubmittedReviewerMessage
from bluebottle.funding.models import FundingPlatformSettings
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, DonorFactory, RewardFactory, \
    BankAccountFactory, PlainPayoutAccountFactory
from bluebottle.funding.tests.utils import generate_mock_bank_account
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.utils import TriggerTestCase


class PlainFundingTriggerTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        self.funding.bank_account = generate_mock_bank_account()
        self.funding.states.submit(save=True)

    def test_trigger_matching(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.partially_funded.value)
        # Add amount matched funding to complete the project should transition it to succeeded
        self.funding.amount_matching = Money(500, 'EUR')
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.succeeded.value)

    def test_trigger_lower_target(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.partially_funded.value)
        # Lower target of the project should transition it to succeeded
        self.funding.target = Money(500, 'EUR')
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.succeeded.value)


class DonorTriggerTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            deadline=now() + timedelta(days=10),
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        bank_account = generate_mock_bank_account()
        self.funding.bank_account = bank_account
        self.funding.states.submit(save=True)
        self.funding.states.approve(save=True)
        self.donor = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        self.payment = StripePaymentFactory.create(donation=self.donor)
        self.payment.states.succeed(save=True)

    def test_succeed_anonymous_reward(self):
        settings = FundingPlatformSettings.load()
        settings.allow_anonymous_rewards = False
        settings.save()

        donor = DonorFactory.create(
            activity=self.funding, amount=Money(500, 'EUR'), reward=RewardFactory.create(), user=None
        )
        payment = StripePaymentFactory.create(donation=donor)
        payment.states.succeed(save=True)

        donor.refresh_from_db()
        self.assertEqual(donor.status, 'succeeded')
        self.assertIsNone(donor.reward)

    def test_succeed_anonymous_reward_allowed(self):

        reward = RewardFactory.create()
        donor = DonorFactory.create(
            activity=self.funding, amount=Money(500, 'EUR'), reward=reward, user=None
        )
        self.assertEqual(donor.reward, reward)
        payment = StripePaymentFactory.create(donation=donor)
        payment.states.succeed(save=True)

        donor.refresh_from_db()

        self.assertEqual(donor.status, 'succeeded')
        self.assertEqual(donor.reward, reward)

    def test_change_donor_amount(self):
        self.assertEqual(self.donor.amount, Money(500, 'EUR'))
        self.assertEqual(self.donor.payout_amount, Money(500, 'EUR'))
        contribution = self.donor.contributions.get()
        self.assertEqual(contribution.value, Money(500, 'EUR'))
        self.assertEqual(self.funding.amount_donated, Money(500, 'EUR'))

        self.donor.amount = Money(200, 'EUR')
        self.donor.payout_amount = Money(200, 'EUR')
        self.donor.save()

        self.funding.refresh_from_db()
        self.assertEqual(self.donor.amount, Money(200, 'EUR'))
        self.assertEqual(self.donor.payout_amount, Money(200, 'EUR'))
        contribution = self.donor.contributions.get()
        self.assertEqual(contribution.value, Money(200, 'EUR'))
        self.assertEqual(self.funding.amount_donated, Money(200, 'EUR'))

        self.donor.payout_amount = Money(250, 'USD')
        self.donor.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.donor.amount, Money(200, 'EUR'))
        self.assertEqual(self.donor.payout_amount, Money(250, 'USD'))
        contribution = self.donor.contributions.get()
        self.assertEqual(contribution.value, Money(250, 'USD'))
        self.assertEqual(self.funding.amount_donated, Money(375, 'EUR'))

    def test_donor_activity_refunded(self):
        """
        Test that donation ends up as activity_refund when refunding a funding activity
        """
        self.assertEqual(self.donor.amount, Money(500, 'EUR'))
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()

        payment_intent = stripe.PaymentIntent('some intent id')

        charge = stripe.Charge('charge-id')

        payment_intent.latest_charge = charge

        with mock.patch(
            "stripe.PaymentIntent.retrieve", return_value=payment_intent
        ):
            with mock.patch("stripe.Refund.create"):
                with mock.patch(
                    "stripe.Charge.retrieve", return_value=charge
                ):
                    self.assertEqual(self.funding.status, "partially_funded")
                    self.funding.states.refund(save=True)
                    self.donor.refresh_from_db()
                    self.payment.states.refund(save=True)

        self.donor.refresh_from_db()
        self.assertEqual(self.donor.status, 'activity_refunded')

    def test_donor_deleted(self):
        self.assertEqual(self.funding.amount_donated, Money(500, 'EUR'))

        self.donor.delete()

        self.assertEqual(self.funding.amount_donated, Money(0, 'EUR'))


class FundingTriggersTestCase(TriggerTestCase):
    factory = FundingFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

        image = ImageFactory()
        payout_account = PlainPayoutAccountFactory.create(
            status='verified'
        )
        bank_acount = BankAccountFactory.create(
            status='verified',
            connect_account=payout_account
        )

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'deadline': now() + timedelta(days=20),
            'target': Money(1000, 'EUR'),
            'title': 'Yeah',
            'image': image,
            'bank_account': bank_acount,

        }
        super().setUp()

    def create(self):
        self.model = self.factory.create(**self.defaults)
        BudgetLineFactory.create(activity=self.model)

    def test_submit(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertNotificationEffect(FundingSubmittedReviewerMessage)
            self.assertNotificationEffect(FundingSubmittedMessage)
            self.assertNoNotificationEffect(ActivitySubmittedReviewerNotification)
            self.assertNoNotificationEffect(ActivitySubmittedNotification)

    def test_approve(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve()

        with self.execute():
            self.assertNotificationEffect(FundingApprovedMessage)
            self.assertNoNotificationEffect(ActivityApprovedNotification)

    def test_needs_work(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.request_changes()

        with self.execute():
            self.assertNotificationEffect(FundingNeedsWorkMessage)
            self.assertNoNotificationEffect(ActivityNeedsWorkNotification)

    def test_reject(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.reject()

        with self.execute():
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
            self.assertNotificationEffect(FundingRejectedMessage)
            self.assertNoNotificationEffect(ActivityRejectedNotification)
