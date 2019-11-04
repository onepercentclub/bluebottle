import json

from django.core import mail
from django.urls import reverse

from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory, PlainPayoutAccountFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class PaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(PaymentTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory(can_pledge=True)
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.donation_url = reverse('funding-donation-list')
        self.payment_url = reverse('pledge-payment-list')

        self.data = {
            'data': {
                'type': 'payments/pledge-payments',
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
        mail.outbox = []

    def test_create_payment(self):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'succeeded')
        self.assertEqual(data['included'][0]['attributes']['status'], 'succeeded')
        # Check that donation mails are send
        self.assertEqual(len(mail.outbox), 2)

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
            data=json.dumps(self.data)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PledgePayoutAccountTestCase(BluebottleTestCase):

    def setUp(self):
        super(PledgePayoutAccountTestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        PledgePaymentProviderFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.payout_account = PlainPayoutAccountFactory.create(
            status='verified',
            owner=self.user
        )

        self.payout_account_url = reverse('payout-account-list')
        self.bank_account_url = reverse('pledge-external-account-list')

        self.data = {
            'data': {
                'type': 'payout-accounts/pledge-external-accounts',
                'attributes': {
                    'account-number': '123456789',
                    'account-holder-name': 'Habari Gani'
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
        self.assertEqual(data['data']['attributes']['account-number'], '123456789')

        response = self.client.get(self.payout_account_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_details = get_included(response, 'payout-accounts/pledge-external-accounts')
        self.assertEqual(bank_details['attributes']['account-number'], '123456789')
        self.assertEqual(bank_details['attributes']['account-holder-name'], 'Habari Gani')
