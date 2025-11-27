import json
from builtins import object

import mock
import munch
import stripe
from django.core import mail
from django.urls import reverse
from moneyed import Money
from munch import munchify
from rest_framework import status

from bluebottle.funding.models import Donor
from bluebottle.funding.tests.factories import (
    FundingFactory, DonorFactory, BudgetLineFactory
)
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentIntentFactory,
    ExternalAccountFactory
)
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentProviderFactory,
    StripePayoutAccountFactory
)
from bluebottle.grant_management.models import GrantPayment
from bluebottle.grant_management.tests.factories import GrantPaymentFactory
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
        self.bank_account = ExternalAccountFactory.create(
            connect_account=StripePayoutAccountFactory.create(
                status="verified", account_id="test-account-id"
            )
        )
        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        self.donation = DonorFactory.create(activity=self.funding)
        self.intent = StripePaymentIntentFactory.create(
            intent_id='some-intent-id',
            donation=self.donation
        )
        self.webhook = reverse('stripe-intent-webhook')

    def test_success(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.intent.intent_id

        transfer = stripe.Transfer(data['object']['latest_charge']['transfer'])
        transfer.update({
            'id': data['object']['latest_charge']['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        charge = stripe.Charge('some charge id')
        charge.update({
            'status': 'succeeded',
            'transfer': transfer.id,
            'refunded': False
        })

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'status': 'succeeded',
            'latest_charge': charge.id
        })
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent('payment_intent.succeeded', data)
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                with mock.patch(
                    'stripe.Charge.retrieve',
                    return_value=charge
                ):
                    with mock.patch(
                        'stripe.PaymentIntent.retrieve',
                        return_value=payment_intent
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

    def test_pending(self):
        with open('bluebottle/funding_stripe/tests/files/payment_webhook_pending.json') as hook_file:
            data = json.load(hook_file)
            data['payment_intent'] = self.intent.intent_id

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.pending', {'object': {'payment_intent': self.intent.intent_id}}
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
        payment = self.intent.get_payment()

        donation = Donor.objects.get(pk=self.donation.pk)

        self.assertEqual(payment.status, 'pending')
        self.assertEqual(donation.status, 'succeeded')
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
        self.test_failed()
        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donor.objects.get(pk=self.donation.pk)

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

        charge = stripe.Charge('some charge id')
        charge.update({
            'status': 'succeeded',
            'transfer': transfer.id,
            'refunded': False
        })

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'status': 'succeeded',
            'latest_charge': charge.id
        })
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent('payment_intent.succeeded', data)
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                with mock.patch(
                    'stripe.Charge.retrieve',
                    return_value=charge
                ):
                    with mock.patch(
                        'stripe.PaymentIntent.retrieve',
                        return_value=payment_intent
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
        self.test_success()

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
        self.test_success()
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
        self.test_success()

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

    def test_grant_payment_success(self):
        intent_id = 'pi_123456789'
        checkout_id = 'cs_123456789'
        GrantPaymentFactory.create(
            intent_id=intent_id,
            checkout_id=checkout_id,
        )

        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = intent_id

        transfer = stripe.Transfer(data['object']['latest_charge']['transfer'])
        transfer.update({
            'id': data['object']['latest_charge']['transfer'],
            'amount': 2500,
            'currency': 'eur'
        })

        charge = stripe.Charge('some charge id')
        charge.update({
            'status': 'succeeded',
            'transfer': transfer.id,
            'refunded': False,
            "balance_transaction": munchify({
                "id": "txn_123456789",
                "object": "balance_transaction",
                "available_on": 1734606300
            })
        })

        payment_intent = stripe.PaymentIntent(intent_id)
        payment_intent.update({
            'status': 'succeeded',
            'latest_charge': charge
        })
        checkout = stripe.checkout.Session(
            checkout_id
        )
        checkout.update({
            'payment_intent': intent_id
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent('payment_intent.succeeded', data)
        ):
            with mock.patch(
                'stripe.Transfer.retrieve',
                return_value=transfer
            ):
                with mock.patch(
                    'stripe.Charge.retrieve',
                    return_value=charge
                ):
                    with mock.patch(
                        'stripe.PaymentIntent.retrieve',
                        return_value=payment_intent
                    ):
                        with mock.patch(
                            'stripe.checkout.Session.retrieve',
                            return_value=checkout
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

        grant_payment = GrantPayment.objects.get(intent_id=intent_id)
        self.assertEqual(grant_payment.status, 'succeeded')


class StripeConnectWebhookTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripeConnectWebhookTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()

        self.payout_account = StripePayoutAccountFactory.create(
            owner=self.user,
            account_id="test-account-id",
            payouts_enabled=False,
            payments_enabled=False,
            verified=False,
        )

        external_account = ExternalAccountFactory.create(
            connect_account=self.payout_account,
            account_id='some-bank-token'
        )
        self.external_account = external_account
        self.funding = FundingFactory.create(bank_account=external_account)
        self.funding.initiative.states.submit(save=True)
        BudgetLineFactory.create(activity=self.funding)
        self.webhook = reverse("stripe-connect-webhook")

        external_account = stripe.BankAccount(external_account.account_id)
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
            'account': 'acct_1032D82eZvKYlo2C',
            "requirements": {
                "eventually_due": [],
                "currently_due": [],
                "past_due": [],
                "pending_verification": [],
            },
            "future_requirements": {
                "eventually_due": [],
                "currently_due": [],
                "past_due": [],
                "pending_verification": [],
            },
        }))

        external_accounts = stripe.ListObject()
        external_accounts.data = [external_account]
        external_accounts.update({
            'total_count': 1,
        })

        self.connect_account = stripe.Account(self.payout_account.account_id)
        self.connect_account.update(
            munch.munchify(
                {
                    "country": "NL",
                    "charges_enabled": True,
                    "payouts_enabled": True,
                    "business_type": "individual",
                    "requirements": {
                        "disabled": False,
                        "eventually_due": [],
                        "currently_due": [],
                        "past_due": [],
                        "pending_verification": [],
                        "disabled_reason": "",
                    },
                    "future_requirements": {
                        "eventually_due": [],
                        "currently_due": [],
                        "past_due": [],
                        "pending_verification": [],
                    },
                    "individual": {
                        "verification": {
                            "status": "verified",
                            "document": {
                                "back": None,
                                "details": None,
                                "details_code": None,
                                "front": "file_12345",
                            },
                        },
                        "requirements": {
                            "eventually_due": [],
                            "currently_due": [],
                            "past_due": [],
                            "pending_verification": [],
                        },
                    },
                    "external_accounts": external_accounts,
                }
            )
        )

    def load_connect_account_fixture(self, filename):
        fixture_path = f"bluebottle/funding_stripe/tests/files/{filename}"
        with open(fixture_path) as hook_file:
            data = munch.munchify(json.load(hook_file))

        data.id = self.payout_account.account_id

        if data.external_accounts.data:
            data.external_accounts.data[0].id = self.external_account.account_id
            data.external_accounts.data[0].account = data.id

        self.connect_account = data

    def execute_hook(self):
        mail.outbox = []

        data = {"object": self.connect_account}
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'account.updated', data
            )
        ):
            response = self.client.post(
                reverse("stripe-connect-webhook"),
                HTTP_STRIPE_SIGNATURE="some signature",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payout_account.refresh_from_db()
        self.funding.refresh_from_db()

    def approve(self):
        self.funding.initiative.status = "approved"
        self.funding.initiative.save()
        self.funding.status = "open"
        self.funding.save()

    def verify(self):
        self.payout_account.verified = True
        self.payout_account.payments_enabled = True
        self.payout_account.payouts_enabled = True

        self.payout_account.save()

    def test_verified(self):
        self.execute_hook()

        self.assertEqual(self.payout_account.status, 'verified')
        message = mail.outbox[0]
        self.assertEqual(
            message.subject, u'Your identity has been verified on Test'
        )
        self.assertTrue(
            self.funding.get_absolute_url() in message.body
        )

    def test_incomplete(self):
        self.verify()
        # Missing fields
        self.connect_account.payouts_enabled = False
        self.connect_account.requirements = {
            "eventually_due": ["individual.document.front"]
        }

        self.execute_hook()

        self.assertEqual(self.payout_account.status, "incomplete")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Action required for your crowdfunding campaign"
        )

    def test_incomplete_open(self):
        self.verify()
        self.approve()

        self.connect_account.requirements = {
            "eventually_due": ["individual.document.front"]
        }
        self.execute_hook()

        self.assertEqual(self.payout_account.status, "incomplete")

        self.assertEqual(len(mail.outbox), 3)

        self.assertEqual(
            mail.outbox[0].subject, "Action required for your crowdfunding campaign"
        )

        self.assertEqual(
            mail.outbox[1].subject, "Live campaign identity verification failed!"
        )
        self.assertEqual(
            mail.outbox[2].subject, "Live campaign identity verification failed!"
        )

    def test_incomplete_open_charges_disabled(self):
        self.verify()
        self.approve()

        self.connect_account.charges_enabled = False
        self.connect_account.requirements = {
            "eventually_due": ["individual.document.front"]
        }
        self.execute_hook()

        self.assertEqual(self.payout_account.status, "disabled")
        self.assertEqual(self.funding.status, "on_hold")

        self.connect_account.charges_enabled = True
        self.connect_account.requirements = {
            "eventually_due": []
        }
        self.execute_hook()

        self.payout_account.refresh_from_db()
        self.assertEqual(self.payout_account.status, "verified")
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, "open")

    def test_document_rejected(self):
        self.verify()
        self.connect_account.individual.verification.details = (
            "this passport smells fishy"
        )
        self.connect_account.individual.verification.status = "unverified"
        self.connect_account.requirements = {
            "eventually_due": ["individual.document.front"]
        }

        self.execute_hook()

        self.assertEqual(self.payout_account.status, "incomplete")

        message = mail.outbox[0]
        self.assertEqual(
            message.subject, "Action required for your crowdfunding campaign"
        )
        self.assertTrue("/activities/stripe/kyc" in message.body)

    def test_payouts_disabled(self):
        self.connect_account.payouts_enabled = False
        self.execute_hook()
        self.assertEqual(self.payout_account.status, "incomplete")

    def test_tos_reaccept(self):
        self.payout_account.tos_accepted = True
        self.payout_account.save(run_triggers=False)

        self.connect_account.requirements = munch.munchify({
            'eventually_due': ['tos_acceptance.date', 'tos_acceptance.ip']
        })
        self.execute_hook()
        self.assertFalse(self.payout_account.tos_accepted)

    def test_company_non_profit_verified(self):
        self.load_connect_account_fixture("connect_webhook_company_verified.json")

        with mock.patch(
            'stripe.Account.retrieve',
            return_value=self.connect_account
        ):
            self.execute_hook()

        self.assertEqual(self.payout_account.status, 'verified')
        self.assertTrue(self.payout_account.verified)
        self.assertEqual(self.payout_account.business_type, 'non_profit')

    def test_individual_fixture_verified(self):
        self.load_connect_account_fixture("connect_webhook_indinvidual_verified.json")

        self.execute_hook()

        self.assertEqual(self.payout_account.status, 'verified')
        self.assertTrue(self.payout_account.verified)
        self.assertEqual(self.payout_account.business_type, 'individual')
        self.assertEqual(self.payout_account.requirements, [])
