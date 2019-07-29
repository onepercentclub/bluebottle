import mock

import bunch

import stripe

from django.db import ProgrammingError


from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory
from bluebottle.funding_stripe.transitions import StripePaymentTransitions
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class StripePaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        StripePaymentProviderFactory.create()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

        self.payment_intent = stripe.PaymentIntent('some intent id')
        self.payment_intent.update({
            'client_secret': 'some client secret',
            'charges': [stripe.Charge('some charge id')]
        })

    def test_create(self):
        payment = StripePayment(donation=self.donation)

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            payment.save()

        self.assertEqual(payment.intent_id, self.payment_intent.id)
        self.assertEqual(payment.client_secret, self.payment_intent.client_secret)
        self.assertEqual(payment.status, StripePaymentTransitions.values.new)

    def test_refund(self):
        payment = StripePayment(donation=self.donation)
        payment.transitions.succeed()

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            payment.save()

        with mock.patch('stripe.PaymentIntent.retrieve', return_value=self.payment_intent):
            with mock.patch('stripe.Charge.refund', return_value=self.payment_intent.charges[0]):
                payment.transitions.request_refund()

        self.assertEqual(payment.status, StripePaymentTransitions.values.refund_requested)


class ConnectAccountTestCase(BluebottleTestCase):
    def setUp(self):
        account_id = 'some-connect-id'
        self.check = StripePayoutAccount(owner=BlueBottleUserFactory.create(), country='NL', account_id=account_id)

        self.connect_account = stripe.Account(account_id)
        self.connect_account.update({
            'country': self.check.country,
            'individual': bunch.bunchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
                'verification': {
                    'status': 'verified',
                }
            }),
            'requirements': bunch.bunchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),
            'external_accounts': bunch.bunchify({
                'data': []
            })
        })

        super(ConnectAccountTestCase, self).setUp()

    def test_save(self):
        self.check.account_id = None
        with mock.patch(
            'stripe.Account.create', return_value=self.connect_account
        ) as create:
            self.check.save()
            create.assert_called_with(
                country=self.check.country,
                metadata={'tenant_name': u'test', 'tenant_domain': u'testserver', 'member_id': self.check.owner.pk},
                settings={'payments': {'statement_descriptor': u''}, 'payouts': {'schedule': {'interval': 'manual'}}},
                business_type='individual',
                type='custom'
            )

            self.assertEqual(self.check.account.id, self.connect_account.id)

            self.assertEqual(
                self.check.account_id,
                self.connect_account.id
            )

    def test_save_already_created(self):
        with mock.patch(
            'stripe.Account.create', return_value=self.connect_account
        ) as create:
            self.check.save()
            self.assertEqual(create.call_count, 0)

    def test_update(self):
        self.check.save()
        token = 'some-token'

        with mock.patch(
            'stripe.Account.modify', return_value=self.connect_account
        ) as modify:
            self.check.update(token)
            self.assertEqual(self.check.account.id, self.connect_account.id)
            modify.assert_called_with(self.check.account_id, account_token=token)

    def test_account(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ) as retrieve:
            self.assertTrue(isinstance(self.check.account, stripe.Account))
            self.assertEqual(self.check.account.id, self.connect_account.id)

            retrieve.assert_called_once_with(self.check.account_id)

    def test_verified(self):
        self.connect_account.requirements.eventually_due = []
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertTrue(self.check.verified)

    def test_not_verified(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertFalse(self.check.verified)

    def test_required(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertEqual(self.check.required, ['external_accounts', 'individual.dob.month'])

    def test_disabled(self):
        self.connect_account.requirements.disabled = True
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertTrue(self.check.disabled)

    def test_not_disabled(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertFalse(self.check.disabled)

    def test_individual(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            self.assertEqual(
                self.check.individual,
                self.connect_account.individual
            )


class StripeExternalAccountTestCase(BluebottleTestCase):
    def setUp(self):
        account_id = 'some-connect-id'
        external_account_id = 'some-bank-token'

        self.check = StripePayoutAccount(owner=BlueBottleUserFactory.create(), country='NL', account_id=account_id)
        self.check.save()

        self.external_account = ExternalAccount(connect_account=self.check, account_id=external_account_id)

        self.connect_external_account = stripe.BankAccount(external_account_id)

        self.connect_external_account.update({
            'object': 'bank_account',
            'account_holder_name': 'Jane Austen',
            'account_holder_type': 'individual',
            'bank_name': 'STRIPE TEST BANK',
            'country': 'US',
            'currency': 'usd',
            'fingerprint': '1JWtPxqbdX5Gamtc',
            'last4': '6789',
            'metadata': {
                'order_id': '6735'
            },
            'routing_number': '110000000',
            'status': 'new',
            'account': 'acct_1032D82eZvKYlo2C'
        })

        self.connect_account = stripe.Account(account_id)
        self.connect_account.update({
            'country': self.check.country,
            'individual': bunch.bunchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
            }),
            'requirements': bunch.bunchify({
                'eventually_due': ['external_accounts'],
                'disabled': False
            }),
            'external_accounts': stripe.ListObject([])
        })

        super(StripeExternalAccountTestCase, self).setUp()

    def test_save(self):
        self.external_account.account_id = None
        with mock.patch(
            'stripe.Account.create_external_account', return_value=self.connect_account
        ) as create:
            with mock.patch(
                'stripe.Account.retrieve', return_value=self.connect_account
            ):
                self.external_account.create('some-token')
                create.assert_called_with(
                    self.check.account_id,
                    external_account='some-token',
                )

                self.assertEqual(self.check.account.id, self.connect_account.id)

                self.assertEqual(
                    self.check.account_id,
                    self.connect_account.id
                )

    def test_save_already_created(self):
        self.assertRaises(
            ProgrammingError,
            self.external_account.create,
            'other-token'
        )

    def test_retrieve(self):
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ) as retrieve_account:
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=self.connect_external_account
            ) as retrieve_external_account:
                self.assertEqual(
                    self.external_account.account.id,
                    self.connect_external_account.id
                )
                self.assertEqual(
                    self.external_account.account.last4,
                    self.connect_external_account.last4
                )

                retrieve_external_account.assert_called_with(self.external_account.account_id)
                retrieve_account.assert_called_with(self.check.account_id)

    def test_retrieve_allready_in_account(self):
        list_object = stripe.ListObject()
        list_object['data'] = [self.connect_external_account]

        self.connect_account.external_accounts = list_object

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ) as retrieve_account:
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=self.connect_external_account
            ) as retrieve_external_account:
                self.assertEqual(
                    self.external_account.account.id,
                    self.connect_external_account.id
                )
                self.assertEqual(
                    self.external_account.account.last4,
                    self.connect_external_account.last4
                )

                retrieve_account.assert_called_with(self.check.account_id)
                self.assertEqual(retrieve_external_account.call_count, 0)
