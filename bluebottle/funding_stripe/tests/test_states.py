import munch
from django.core import mail
from djmoney.money import Money
from mock import patch
import stripe

from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, DonorFactory
from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory, StripeSourcePaymentFactory, \
    StripePaymentFactory, ExternalAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class BaseStripePaymentStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative, target=Money(1000, "EUR")
        )

        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        self.bank_account = ExternalAccountFactory.create(status='verified', connect_account=payout_account)
        self.funding.bank_account = self.bank_account
        self.funding.save()
        self.funding.states.submit()
        self.funding.states.approve(save=True)


class StripeSourcePaymentStateMachineTests(BaseStripePaymentStateMachineTests):

    @patch('stripe.Source.modify')
    def setUp(self, mock_modify):
        super(StripeSourcePaymentStateMachineTests, self).setUp()
        self.donation = DonorFactory.create(activity=self.funding)
        self.payment = StripeSourcePaymentFactory.create(
            charge_token='some_token',
            donation=self.donation
        )

    def test_request_refund(self):
        self.payment.states.succeed(save=True)
        self.assertEqual(self.payment.status, 'succeeded')

        with patch("stripe.Refund.create") as refund_mock:
            self.payment.states.request_refund(save=True)
            refund_mock.assert_called_once()

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'refund_requested')

    def test_refund_activity(self):
        self.payment.states.succeed(save=True)
        self.assertEqual(self.payment.status, 'succeeded')
        self.funding.states.succeed(save=True)

        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            self.funding.states.refund(save=True)
            refund.assert_called_once()

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'refund_requested')

    def test_authorize(self):
        self.payment.states.charge(save=True)
        self.payment.states.authorize(save=True)
        self.assertEqual(self.payment.status, 'pending')

    def test_authorize_donation_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.authorize(save=True)
        self.assertEqual(self.donation.status, 'succeeded')

    def test_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.assertEqual(self.payment.status, 'succeeded')

    def test_succeed_donation_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.assertEqual(self.donation.status, 'succeeded')

    def test_charge(self):
        self.payment.states.charge(save=True)
        self.assertEqual(self.payment.status, 'charged')

    def test_cancel(self):
        self.payment.states.cancel(save=True)
        self.assertEqual(self.payment.status, 'canceled')

    def test_dispute(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.payment.states.dispute(save=True)
        self.assertEqual(self.payment.status, 'disputed')


class StripePaymentStateMachineTests(BaseStripePaymentStateMachineTests):

    @patch('stripe.PaymentIntent.retrieve')
    def test_request_refund(self, mock_retrieve):
        donation = DonorFactory.create(activity=self.funding)
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')

        with patch("stripe.Refund.create"):
            payment.states.request_refund(save=True)
            self.assertEqual(payment.status, "refund_requested")


class StripePayoutAccountStateMachineTests(BluebottleTestCase):

    def setUp(self):
        account_id = 'some-connect-id'
        self.user = BlueBottleUserFactory.create()
        self.account = StripePayoutAccountFactory.create(
            owner=self.user,
            country='NL',
            account_id=account_id
        )
        self.stripe_account = stripe.Account(account_id)
        self.stripe_account.update(
            {
                "country": "NL",
                "charges_enabled": True,
                "individual": munch.munchify(
                    {
                        "email": "jhon@example.com",
                        "verification": {
                            "status": "unverified",
                        },
                        "requirements": munch.munchify(
                            {
                                "eventually_due": [
                                    "first_name",
                                    "last_name",
                                    "dob.year",
                                    "dob.month",
                                    "dob.day",
                                ]
                            }
                        ),
                    }
                ),
                "requirements": munch.munchify(
                    {
                        "eventually_due": [
                            "individual.first_name",
                            "individual.last_name",
                            "individual.dob.year",
                            "individual.dob.month",
                            "individual.dob.day",
                            "external_accounts",
                        ],
                        "disabled": False,
                    }
                ),
                "payouts_enabled": True,
                "external_accounts": munch.munchify({"total_count": 0, "data": []}),
            }
        )

        self.account.update(self.stripe_account)
        self.bank_account = ExternalAccountFactory.create(
            connect_account=self.account,
            status='verified',
            account_id='test-bank-account-id'
        )
        self.funding = FundingFactory.create(
            bank_account=self.bank_account,
            target=Money(1000, "EUR")
        )

    def simulate_webhook(
        self,
        requirements,
        verification_status=None,
        enable_payments=None,
        enable_payouts=None,
    ):
        self.stripe_account.individual.requirements.eventually_due = [
            requirement.replace("individual.", "")
            for requirement in requirements
            if requirement.startswith("individual.")
        ]
        self.stripe_account.requirements.eventually_due = requirements

        if enable_payments is not None:
            self.stripe_account.charges_enabled = enable_payments

        if enable_payouts is not None:
            self.stripe_account.payouts_enabled = enable_payouts

        if verification_status:
            self.stripe_account.individual.verification.status = verification_status

        self.account.update(self.stripe_account)

    def test_initial(self):
        self.assertEqual(self.account.status, 'new')

    def test_pending(self):
        self.simulate_webhook([])

        self.assertEqual(self.account.status, "pending")

    def test_needs_verification(self):
        self.test_pending()

        self.simulate_webhook(["individual.verification.document"])
        self.assertEqual(self.account.status, "incomplete")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Action required for your crowdfunding campaign"
        )

    def test_verify(self):
        self.simulate_webhook([], verification_status="verified")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your identity has been verified")

    def test_needs_verification_pending(self):
        self.test_needs_verification()
        mail.outbox = []

        self.simulate_webhook([], verification_status="verified")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity has been verified')

    def test_reject(self):
        self.test_verify()
        mail.outbox = []

        self.simulate_webhook(
            ["individual.verification.document"], verification_status="rejected"
        )

        self.assertEqual(self.account.status, "incomplete")
        self.assertEqual(
            mail.outbox[0].subject, "Action required for your crowdfunding campaign"
        )

    def test_reject_disable_payments(self):
        self.test_verify()
        mail.outbox = []

        self.simulate_webhook(
            ["individual.verification.document"],
            verification_status="rejected",
            enable_payments=False
        )

        self.assertEqual(self.account.status, "disabled")
        self.assertEqual(
            mail.outbox[0].subject, "Action required for your crowdfunding campaign"
        )


class StripeBankAccountStateMachineTests(BluebottleTestCase):

    def setUp(self):
        account_id = 'some-connect-id'
        self.user = BlueBottleUserFactory.create()
        self.account = StripePayoutAccount(
            owner=self.user,
            country='NL',
            account_id=account_id
        )
        self.stripe_account = stripe.Account(account_id)
        self.stripe_account.update({
            'country': 'NL',
            'individual': munch.munchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': {
                    'status': 'verified',
                },
                'requirements': munch.munchify({
                    'eventually_due': [
                        'external_accounts',
                        'individual.verification.document',
                        'document_type',
                    ]
                }),
            }),
            'requirements': munch.munchify({
                'eventually_due': [
                    'external_accounts',
                    'individual.verification.document.front',
                    'document_type',
                ],
                'disabled': False
            }),
            'external_accounts': munch.munchify({
                'total_count': 0,
                'data': []
            })
        })
        with patch('stripe.Account.retrieve', return_value=self.stripe_account):
            self.account.save()

        self.bank_account = ExternalAccountFactory.create(connect_account=self.account)

    def test_initial(self):
        self.assertEqual(self.bank_account.status, 'unverified')

    def test_account_verifies_bank_accounts(self):
        self.account.states.verify(save=True)
        self.assertEqual(self.account.status, 'verified')
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.status, 'verified')

    def test_2nd_bank_verifies_right_away(self):
        self.account.states.verify(save=True)
        new_bank_account = ExternalAccountFactory.create(connect_account=self.account)
        new_bank_account.refresh_from_db()
        self.assertEqual(new_bank_account.status, 'verified')

    def test_rejeceted_bank_verifies(self):
        self.bank_account.states.reject(save=True)
        self.account.states.verify(save=True)
        self.assertEqual(self.account.status, 'verified')
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.status, 'verified')
