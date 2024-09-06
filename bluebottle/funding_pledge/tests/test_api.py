import json

from django.core import mail
from django.urls import reverse

from rest_framework import status

from bluebottle.funding.tests.factories import (
    FundingFactory, DonorFactory, PlainPayoutAccountFactory
)
from bluebottle.funding_pledge.tests.factories import (
    PledgePaymentProviderFactory, PledgeBankAccountFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class PaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(PaymentTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory(can_pledge=True)
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonorFactory.create(activity=self.funding, user=self.user)

        self.donation_url = reverse('funding-donation-list')
        self.payment_url = reverse('pledge-payment-list')

        self.data = {
            'data': {
                'type': 'payments/pledge-payments',
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
        mail.outbox = []

    def test_create_payment(self):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data["data"]["attributes"]["status"], "succeeded")
        self.assertEqual(data["included"][1]["attributes"]["status"], "succeeded")
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


class PledgePayoutAccountListTestCase(BluebottleTestCase):

    def setUp(self):
        super(PledgePayoutAccountListTestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        PledgePaymentProviderFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
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
        bank_details = self.included_by_type(response, 'payout-accounts/pledge-external-accounts')[0]
        self.assertEqual(bank_details['attributes']['account-number'], '123456789')
        self.assertEqual(bank_details['attributes']['account-holder-name'], 'Habari Gani')

    def test_get_bank_accounts_no_user(self):
        response = self.client.post(self.bank_account_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(
            self.bank_account_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_bank_accounts_other_user(self):
        response = self.client.post(self.bank_account_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(
            self.bank_account_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_get_accounts_no_user(self):
        response = self.client.get(
            self.payout_account_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_accounts_other_user(self):
        response = self.client.get(
            self.payout_account_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)


class PledgePayoutAccountDetailTestCase(BluebottleTestCase):

    def setUp(self):
        super(PledgePayoutAccountDetailTestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        PledgePaymentProviderFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.payout_account = PlainPayoutAccountFactory.create(
            status='verified',
            owner=self.user
        )
        self.bank_account = PledgeBankAccountFactory.create(
            connect_account=self.payout_account
        )

        self.bank_account_url = reverse(
            'pledge-external-account-detail', args=(self.bank_account.pk, )
        )

        self.data = {
            'data': {
                'type': 'payout-accounts/pledge-external-accounts',
                'id': self.bank_account.pk,
                'attributes': {
                    'account-number': '11111111',
                },
            }
        }

    def test_update(self):
        response = self.client.patch(
            self.bank_account_url, data=json.dumps(self.data), user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bank_account.refresh_from_db()

        self.assertEqual(
            self.bank_account.account_number,
            self.data['data']['attributes']['account-number']
        )

    def test_update_no_user(self):
        response = self.client.patch(
            self.bank_account_url, data=json.dumps(self.data)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_no_user(self):
        response = self.client.get(
            self.bank_account_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_other_user(self):
        response = self.client.patch(
            self.bank_account_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_other_user(self):
        response = self.client.get(
            self.bank_account_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
