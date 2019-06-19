import json
import mock

import bunch

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('stripe-payment-list')

        self.data = {
            'data': {
                'type': 'payments/stripe-payments',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributions/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    def test_create_payment(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_payment_other_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_payment_no_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StripeKYCCheckListTestCase(BluebottleTestCase):
    def setUp(self):
        super(StripeKYCCheckListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()

        self.url = reverse('stripe-kyc-check-list')

        self.data = {
            'data': {
                'type': 'kyc-check/stripe',
                'attributes': {
                    'token': 'some-account-token',
                    'country': 'NL',
                }
            }
        }

    def test_create(self):
        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': self.data['data']['attributes']['country'],
            'individual': bunch.bunchify({
                'first_name': 'Jhon',
                'last_name': 'Example',
                'email': 'jhon@example.com',
            }),
            'requirements': bunch.bunchify({
                'eventually_due': ['external_accounts', 'individual.dob.month'],
                'disabled': False
            }),


        })

        with mock.patch('stripe.Account.create', return_value=connect_account) as create_account:
            with mock.patch('stripe.Account.modify', return_value=connect_account) as modify_account:
                response = self.client.post(
                    self.url, data=json.dumps(self.data), user=self.user
                )
                create_account.assert_called_with(country='NL')
                modify_account.assert_called_with('some-connect-id', token='some-account-token')

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['country'],
            self.data['data']['attributes']['country']
        )
        self.assertEqual(
            data['data']['attributes']['disabled'], False
        )
        self.assertEqual(
            data['data']['attributes']['verified'], False
        )
        self.assertEqual(
            data['data']['attributes']['required'],
            ["external_accounts", "individual.dob.month"]
        )
        self.assertEqual(
            data['data']['attributes']['personal-data']['first_name'],
            'Jhon',
        )

        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.user.pk)
        )

    def test_create_no_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
