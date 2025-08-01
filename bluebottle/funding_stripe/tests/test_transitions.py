import mock
import stripe
from moneyed import Money
import munch

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory, BudgetLineFactory
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentFactory, StripePayoutAccountFactory, ExternalAccountFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class StripePaymentTransitionsTestCase(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            duration=30,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        self.payout_account = StripePayoutAccountFactory.create(
            account_id="test-id", status="verified"
        )
        self.bank_account = ExternalAccountFactory.create(
            connect_account=self.payout_account, status='verified'
        )
        self.funding.bank_account = self.bank_account
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        donation = DonorFactory.create(
            amount=Money(150, 'EUR'),
            activity=self.funding,
            status='succeeded'
        )

        self.payment = StripePaymentFactory.create(donation=donation)
        super(StripePaymentTransitionsTestCase, self).setUp()

    def test_refund(self):
        self.payment.states.succeed(save=True)
        payment_intent = stripe.PaymentIntent('some intent id')

        charge = stripe.Charge('charge-id')
        payment_intent.latest_charge = charge.id

        with mock.patch("stripe.PaymentIntent.retrieve", return_value=payment_intent):
            with mock.patch("stripe.Refund.create") as refund_mock:
                self.payment.states.request_refund(save=True)

        self.assertTrue(refund_mock.called_once)

    def test_change_business_type(self):
        self.payout_account.business_type = 'company'
        stripe_payout_account = stripe.Account('some account id')
        stripe_payout_account.individual = munch.munchify({'verification': {'status': 'verified'}})
        stripe_payout_account.requirements = munch.munchify({'eventually_due': []})
        stripe_payout_account.charges_enabled = True
        stripe_payout_account.payouts_enabled = True

        with mock.patch("stripe.Account.modify", return_value=stripe_payout_account) as update_mock:
            self.payout_account.save()
            update_mock.assert_called_with(self.payout_account.account_id, business_type='company')
