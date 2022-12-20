from builtins import object
import json

import munch
import mock
import stripe
from django.core import mail
from django.urls import reverse
from moneyed import Money
from rest_framework import status

from bluebottle.funding.models import Donor
from bluebottle.funding.tests.factories import (
    FundingFactory, DonorFactory, BudgetLineFactory
)
from bluebottle.funding_stripe.models import StripePayoutAccount, StripePaymentProvider
from bluebottle.funding_stripe.models import StripeSourcePayment
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentIntentFactory,
    StripeSourcePaymentFactory,
    ExternalAccountFactory)
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentProviderFactory,
    StripePayoutAccountFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEvent(object):
    def __init__(self, type, data):
        self.type = type
        self.data = munch.munchify(data)


class IntentWebhookTestCase(BluebottleTestCase):

    def setUp(self):
        super(IntentWebhookTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.bank_account = ExternalAccountFactory.create()
        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        self.donation = DonorFactory.create(activity=self.funding)
        self.intent = StripePaymentIntentFactory.create(donation=self.donation)
        self.webhook = reverse('stripe-intent-webhook')

    def test_success(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.intent.intent_id

        transfer = stripe.Transfer(data['object']['charges']['data'][0]['transfer'])
        transfer.update({
            'id': data['object']['charges']['data'][0]['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Stripe might send double success webhooks
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment
        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, 'succeeded')
        self.assertEqual(donation.payout_amount, Money(25, 'EUR'))
        self.assertEqual(payment.status, 'succeeded')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'succeeded')

    def test_failed(self):
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.payment_failed', {'object': {'id': self.intent.intent_id}}
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Stripe might send double failed webhooks
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, 'failed')
        self.assertEqual(payment.status, 'failed')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')

    def test_failed_second_intent_succeeds(self):
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.payment_failed', {'object': {'id': self.intent.intent_id}}
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Stripe might send double failed webhooks
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, 'failed')
        self.assertEqual(payment.status, 'failed')
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')

        second_intent = StripePaymentIntentFactory.create(donation=self.donation, intent_id='some-other-id')
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = second_intent.intent_id

        transfer = stripe.Transfer(data['object']['charges']['data'][0]['transfer'])
        transfer.update({
            'id': data['object']['charges']['data'][0]['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        second_intent.refresh_from_db()
        self.assertEqual(second_intent.payment.pk, payment.pk)

        payment.refresh_from_db()
        donation.refresh_from_db()

        self.assertEqual(donation.status, 'succeeded')
        self.assertEqual(donation.payout_amount, Money(25, 'EUR'))
        self.assertEqual(payment.status, 'succeeded')

    def test_refund(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.intent.intent_id

        transfer = stripe.Transfer(data['object']['charges']['data'][0]['transfer'])
        transfer.update({
            'id': data['object']['charges']['data'][0]['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        with open('bluebottle/funding_stripe/tests/files/intent_webhook_refund.json') as hook_file:
            data = json.load(hook_file)
            data['object']['payment_intent'] = self.intent.intent_id

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, 'refunded')
        self.assertEqual(payment.status, 'refunded')

    def test_refund_no_intent(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.intent.intent_id

        transfer = stripe.Transfer(data['object']['charges']['data'][0]['transfer'])
        transfer.update({
            'id': data['object']['charges']['data'][0]['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        with open('bluebottle/funding_stripe/tests/files/intent_webhook_refund.json') as hook_file:
            data = json.load(hook_file)
            data['object']['payment_intent'] = None

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(response.content, b'Not an intent payment')

    def test_refund_from_requested_refund(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.intent.intent_id

        transfer = stripe.Transfer(data['object']['charges']['data'][0]['transfer'])
        transfer.update({
            'id': data['object']['charges']['data'][0]['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        with mock.patch(
            'bluebottle.funding_stripe.models.StripePayment.refund',
        ):
            self.intent.payment.states.request_refund(save=True)

        with open('bluebottle/funding_stripe/tests/files/intent_webhook_refund.json') as hook_file:
            data = json.load(hook_file)
            data['object']['payment_intent'] = self.intent.intent_id

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.payment.refresh_from_db()

        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, 'refunded')
        self.assertEqual(self.intent.payment.status, 'refunded')


class SourcePaymentWebhookTestCase(BluebottleTestCase):
    def setUp(self):
        super(SourcePaymentWebhookTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.bank_account = ExternalAccountFactory.create()
        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        self.donation = DonorFactory.create(activity=self.funding)

        with mock.patch(
            'stripe.Source.modify'
        ):
            self.payment = StripeSourcePaymentFactory.create(
                source_token='some-source-id',
                donation=self.donation
            )

        self.webhook = reverse('stripe-source-webhook')

    def _refresh(self):
        self.donation = Donor.objects.get(pk=self.donation.pk)
        self.payment = StripeSourcePayment.objects.get(pk=self.payment.pk)

    def test_source_failed(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.failed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Stripe might send double failed webhooks
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'failed')
        self.assertEqual(self.payment.status, 'failed')

    def test_source_canceled(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.canceled', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'failed')
        self.assertEqual(self.payment.status, 'canceled')

    def test_source_chargeable(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }
        charge = stripe.Charge('some charge token')
        charge.update({
            'status': 'succeeded',
            'refunded': False
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.chargeable', data
            )
        ):
            with mock.patch('stripe.Charge.create', return_value=charge) as create_charge:
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )

                create_charge.assert_called_with(
                    amount=int(self.donation.amount.amount * 100),
                    currency=self.donation.amount.currency,
                    metadata={
                        'tenant_name': u'test',
                        'activity_id': self.funding.pk,
                        'activity_title': self.funding.title,
                        'tenant_domain': u'testserver'
                    },
                    source=u'some-source-id',
                    statement_descriptor_suffix=u'Test',
                    transfer_data={
                        'destination': self.funding.bank_account.connect_account.account_id
                    }
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'new')
        self.assertEqual(self.payment.status, 'charged')

    def test_source_chargeable_us(self):
        self.funding.bank_account.connect_account.country = 'US'

        data = {
            'object': {
                'id': self.payment.source_token
            }
        }
        charge = stripe.Charge('some charge token')
        charge.update({
            'status': 'succeeded',
            'refunded': False
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.chargeable', data
            )
        ):
            with mock.patch('stripe.Charge.create', return_value=charge) as create_charge:
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )

                create_charge.assert_called_with(
                    amount=int(self.donation.amount.amount * 100),
                    currency=self.donation.amount.currency,
                    metadata={
                        'tenant_name': u'test',
                        'activity_id': self.funding.pk,
                        'activity_title': self.funding.title,
                        'tenant_domain': u'testserver'
                    },
                    source=u'some-source-id',
                    statement_descriptor_suffix=u'Test',
                    transfer_data={
                        'destination': self.funding.bank_account.connect_account.account_id
                    }
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'new')
        self.assertEqual(self.payment.status, 'charged')

    def test_charge_pending(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)

        data = {
            'object': {
                'id': self.payment.charge_token,
                'payment_intent': None
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.pending', data
            )
        ):

            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'succeeded')
        self.assertEqual(self.payment.status, 'pending')

        data['object']['transfer'] = 'tr_some_id'

        transfer = stripe.Transfer(data['object']['transfer'])
        transfer.update({
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'succeeded')
        self.assertEqual(self.donation.payout_amount, Money(25, 'EUR'))
        self.assertEqual(self.payment.status, 'succeeded')

    def test_charge_succeeded(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)

        data = {
            'object': {
                'id': self.payment.charge_token,
                'transfer': 'tr_some_id',
                'payment_intent': None
            }
        }
        transfer = stripe.Transfer(data['object']['transfer'])
        transfer.update({
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.succeeded', data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Stripe might send double success webhooks
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'succeeded')
        self.assertEqual(self.donation.payout_amount, Money(25, 'EUR'))
        self.assertEqual(self.payment.status, 'succeeded')

    def test_charge_succeeded_intent(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)

        data = {
            'object': {
                'id': 'blabla',
                'transfer': 'tr_some_id',
                'payment_intent': 'pi_23456789'

            }
        }
        transfer = stripe.Transfer(data['object']['transfer'])
        transfer.update({
            'amount': 2500,
            'currency': 'eur'
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.succeeded',
                data
            )
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'new')

    def test_charge_failed(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)

        data = {
            'object': {
                'id': self.payment.charge_token,
                'payment_intent': None
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.failed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'failed')
        self.assertEqual(self.payment.status, 'failed')

    def test_charge_refunded(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)

        data = {
            'object': {
                'id': self.payment.charge_token,
                'payment_intent': None
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.payment.status, 'refunded')
        self.assertEqual(self.donation.status, 'refunded')

    def test_charge_refunded_refund_requested(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)

        with mock.patch(
            'bluebottle.funding_stripe.models.StripeSourcePayment.refund',
        ):
            self.payment.states.request_refund(save=True)

        data = {
            'object': {
                'id': self.payment.charge_token,
                'payment_intent': None
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.payment.status, 'refunded')
        self.assertEqual(self.donation.status, 'refunded')

    def test_charge_dispute_closed(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)

        data = {
            'object': {
                'charge': self.payment.charge_token,
                'status': 'lost',
                'payment_intent': None
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.dispute.closed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, 'refunded')
        self.assertEqual(self.payment.status, 'disputed')


class StripeConnectWebhookTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripeConnectWebhookTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()

        self.connect_account = stripe.Account('some-account-id')

        external_account = stripe.BankAccount('some-bank-token')
        external_account.update(munch.munchify({
            'object': 'bank_account',
            'account_holder_name': 'Jane Austen',
            'account_holder_type': 'individual',
            'bank_name': 'STRIPE TEST BANK',
            'country': 'NL',
            'currency': 'usd',
            'fingerprint': '1JWtPxqbdX5Gamtc',
            'last4': '6789',
            'metadata': {
                'order_id': '6735'
            },
            'routing_number': '110000000',
            'status': 'new',
            'account': 'acct_1032D82eZvKYlo2C'
        }))

        external_accounts = stripe.ListObject()
        external_accounts.data = [external_account]
        external_accounts.update({
            'total_count': 1,
        })

        self.connect_account.update(munch.munchify({
            'country': 'NL',
            'requirements': {
                'disabled': False,
                'eventually_due': [],
                'currently_due': [],
                'past_due': [],
                'pending_verification': [],
                'disabled_reason': ''
            },
            'individual': {
                'verification': {
                    'status': 'verified',
                    'document': {
                        "back": None,
                        "details": None,
                        "details_code": None,
                        "front": "file_12345"
                    }
                },
                'requirements': {
                    'eventually_due': [],
                    'currently_due': [],
                    'past_due': [],
                    'pending_verification': [],
                },
            },
            'external_accounts': external_accounts
        }))

        with mock.patch('stripe.Account.create', return_value=self.connect_account):
            self.payout_account = StripePayoutAccountFactory.create(owner=self.user)

        external_account = ExternalAccountFactory.create(connect_account=self.payout_account)

        self.funding = FundingFactory.create(bank_account=external_account)
        self.funding.initiative.states.submit(save=True)
        BudgetLineFactory.create(activity=self.funding)
        self.webhook = reverse('stripe-connect-webhook')

    def test_verified(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }

        mail.outbox = []

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payout_account.refresh_from_db()

        message = mail.outbox[0]

        self.assertEqual(self.payout_account.status, 'verified')
        self.assertEqual(
            message.subject, u'Your identity has been verified'
        )
        self.assertTrue(
            self.funding.get_absolute_url() in message.body
        )
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'submitted')

    def test_incomplete(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }
        # Missing fields
        self.connect_account.individual.requirements.eventually_due = ['dob.day']
        self.connect_account.individual.requirements.currently_due = []
        self.connect_account.individual.requirements.past_due = []
        self.connect_account.individual.requirements.pending_verification = False
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payout_account.refresh_from_db()
        self.assertEqual(self.payout_account.status, 'rejected')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity verification could not be verified!')

        # Missing fields
        self.connect_account.individual.requirements.eventually_due = []
        self.connect_account.individual.requirements.currently_due = ['dob.day']
        self.connect_account.individual.requirements.past_due = []
        self.connect_account.individual.requirements.pending_verification = []

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payout_account.refresh_from_db()
        self.funding.refresh_from_db()
        self.assertEqual(self.payout_account.status, 'rejected')

        # No missing fields. Should be approved now
        self.connect_account.individual.requirements.eventually_due = []
        self.connect_account.individual.requirements.currently_due = []
        self.connect_account.individual.requirements.past_due = []
        self.connect_account.individual.requirements.pending_verification = []

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout_account = StripePayoutAccount.objects.get(pk=self.payout_account.pk)
        self.funding.refresh_from_db()
        self.assertEqual(payout_account.status, u'verified')
        self.assertEqual(mail.outbox[1].subject, 'Your identity has been verified')
        self.assertEqual(mail.outbox[1].bcc, [])

    def test_incomplete_open(self):
        mail.outbox = []
        self.funding.status = 'open'
        self.funding.save()
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }
        # Missing fields
        self.connect_account.individual.requirements.eventually_due = ['dob.day']
        self.connect_account.individual.requirements.currently_due = []
        self.connect_account.individual.requirements.past_due = []
        self.connect_account.individual.requirements.pending_verification = False
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payout_account.refresh_from_db()
        self.assertEqual(self.payout_account.status, 'rejected')
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[0].subject, 'Your identity verification could not be verified!')
        self.assertEqual(mail.outbox[1].subject, 'Live campaign identity verification failed!')
        self.assertEqual(mail.outbox[2].subject, 'Live campaign identity verification failed!')

    def test_pending(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }
        # Missing fields
        self.connect_account.individual.requirements.eventually_due = []
        self.connect_account.individual.requirements.currently_due = []
        self.connect_account.individual.requirements.past_due = []
        self.connect_account.individual.requirements.pending_verification = ['document.front']

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout_account = StripePayoutAccount.objects.get(pk=self.payout_account.pk)
        self.assertEqual(payout_account.status, 'pending')

    def test_disabled(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }

        self.connect_account.requirements.disabled_reason = "you're up to no good"

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout_account = StripePayoutAccount.objects.get(pk=self.payout_account.pk)

        self.assertEqual(payout_account.status, 'rejected')

    def test_document_rejected(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }

        self.connect_account.individual.verification.document.details = "this passport smells fishy"

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout_account = StripePayoutAccount.objects.get(pk=self.payout_account.pk)

        self.assertEqual(payout_account.status, 'rejected')

        message = mail.outbox[0]
        self.assertEqual(
            message.subject, u'Your identity verification could not be verified!'
        )
        self.assertTrue(
            '/initiatives/activities/funding/kyc' in message.body
        )

    def test_no_account(self):
        data = {
            "object": {
                "id": self.payout_account.account_id,
                "object": "account"
            }
        }

        self.connect_account.individual = None

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            with mock.patch('stripe.Account.retrieve', return_value=self.connect_account):
                response = self.client.post(
                    reverse('stripe-connect-webhook'),
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout_account = StripePayoutAccount.objects.get(pk=self.payout_account.pk)

        self.assertEqual(payout_account.status, 'incomplete')
        self.assertEqual(len(mail.outbox), 0)
