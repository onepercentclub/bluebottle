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
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(status='verified')
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
        self.assertEqual(self.account.status, 'new')

    def test_verify(self):
        self.account.states.verify(save=True)
        self.assertEqual(self.account.status, 'verified')

    def test_accept_mail(self):
        self.account.states.verify(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity has been verified')

    def test_reject(self):
        self.account.states.reject(save=True)
        self.assertEqual(self.account.status, 'rejected')

    def test_reject_mail(self):
        self.account.states.reject(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity verification could not be verified!')


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
