import json

from django.urls import reverse
from djmoney.money import Money
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory, PlainPayoutAccountFactory
from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included

success_response = {
    'status': 'success',
    'data': {
        'status': 'successful',
        'amount': 1000,
        'currency': 'NGN'
    }
}

failed_response = {
    'status': 'success',
    'data': {
        'status': 'failed',
        'amount': 1000,
        'currency': 'NGN'
    }
}


class FlutterwavePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(FlutterwavePaymentTestCase, self).setUp()
        self.provider = FlutterwavePaymentProviderFactory.create()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, amount=Money(1000, 'NGN'), user=self.user)

        self.payment_url = reverse('flutterwave-payment-list')

        self.tx_ref = "{}-{}".format(self.provider.prefix, self.donation.id)

        self.data = {
            'data': {
                'type': 'payments/flutterwave-payments',
                'attributes': {
                    'tx-ref': self.tx_ref
                },
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributors/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=success_response)
    def test_create_payment_success(self, flutterwave_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'succeeded')
        self.assertEqual(data['data']['attributes']['tx-ref'], self.tx_ref)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'succeeded')

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=success_response)
    def test_create_anonymous_payment_success(self, flutterwave_post):
        donation = DonationFactory.create(
            activity=self.funding,
            amount=Money(1000, 'NGN'),
            user=self.user,
            client_secret='348576245976234597'
        )
        self.tx_ref = "{}-{}".format(self.provider.prefix, donation.id)

        self.data = {
            'data': {
                'type': 'payments/flutterwave-payments',
                'attributes': {
                    'tx-ref': self.tx_ref
                },
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributors/donations',
                            'id': donation.pk,
                        }
                    }
                }
            }
        }

        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            HTTP_AUTHORIZATION='Donation {}'.format(donation.client_secret)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'succeeded')
        self.assertEqual(data['data']['attributes']['tx-ref'], self.tx_ref)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'succeeded')

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=failed_response)
    def test_create_payment_failure(self, flutterwave_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'failed')
        self.assertEqual(data['data']['attributes']['tx-ref'], self.tx_ref)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=success_response)
    def test_create_payment_duplicate(self, flutterwave_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_donation = DonationFactory.create(activity=self.funding, amount=Money(1000, 'NGN'), user=self.user)
        self.data['data']['relationships']['donation']['data']['id'] = new_donation.id

        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FlutterwavePayoutAccountTestCase(BluebottleTestCase):

    def setUp(self):
        super(FlutterwavePayoutAccountTestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        FlutterwavePaymentProviderFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.payout_account = PlainPayoutAccountFactory.create(
            status='verified',
            owner=self.user
        )

        self.payout_account_url = reverse('payout-account-list')
        self.bank_account_url = reverse('flutterwave-external-account-list')

        self.data = {
            'data': {
                'type': 'payout-accounts/flutterwave-external-accounts',
                'attributes': {
                    'bank-code': '044',
                    'account-number': '123456789',
                    'account-holder-name': 'Jolof Rice'
                },
                'relationships': {
                    'connect-account': {
                        'data': {
                            'id': self.payout_account.id,
                            'type': 'payout-accounts/plains'
                        }
                    }
                }
            }
        }

    def test_create_bank_account(self):
        response = self.client.post(self.bank_account_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['bank-code'], '044')

        response = self.client.get(self.payout_account_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_details = get_included(response, 'payout-accounts/flutterwave-external-accounts')
        self.assertEqual(bank_details['attributes']['bank-code'], '044')
