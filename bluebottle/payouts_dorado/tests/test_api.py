import json

from django.contrib.auth.models import Group
from django.urls import reverse
from moneyed import Money
from rest_framework import status
from rest_framework.authtoken.models import Token

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory, BudgetLineFactory
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, \
    StripePaymentFactory, StripePayoutAccountFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class TestPayoutApi(BluebottleTestCase):
    """
    Test Payouts API
    """

    def setUp(self):
        super(TestPayoutApi, self).setUp()
        self.client = JSONAPITestClient()
        self.plain_user = BlueBottleUserFactory.create()
        self.plain_token = Token.objects.create(user=self.plain_user)
        self.finance_user = BlueBottleUserFactory.create()
        self.token = Token.objects.create(user=self.finance_user)
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.finance_user)

        payout_account = StripePayoutAccountFactory.create(status='verified')
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account)

        self.funding = FundingFactory.create()

        self.funding.bank_account = self.bank_account

        BudgetLineFactory.create_batch(2, activity=self.funding)

        self.funding.initiative.states.submit()
        self.funding.initiative.states.approve(save=True)
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        donations = DonorFactory.create_batch(
            4,
            activity=self.funding,
            amount=Money(35, 'EUR'),
            status='succeeded'
        )
        for donation in donations:
            StripePaymentFactory.create(
                status='succeeded',
                donation=donation
            )

        self.funding.states.succeed(save=True)
        self.payout = self.funding.payouts.first()
        self.payout_url = reverse('payout-details', kwargs={'pk': self.payout.id})

    def test_payouts_api_access_denied_for_anonymous(self):
        """
        """
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payouts_api_access_denied_for_normal_user(self):
        """
        """
        response = self.client.get(self.payout_url,
                                   HTTP_AUTHORIZATION="Token {}".format(self.plain_token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payouts_api_access_granted_for_power_user(self):
        """
        """
        response = self.client.get(self.payout_url,
                                   HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payouts_api_update_payout_status(self):
        """
        Update payout status
        """
        # Possible statuses from Dorado
        statuses = [
            ('reset', 'new'),
            ('new', 'scheduled'),
            ('scheduled', 'scheduled'),
            ('started', 'started'),
            ('success', 'succeeded'),
            ('confirmed', 'succeeded'),
            ('failed', 'failed'),
        ]

        payout_url = reverse('payout-details', kwargs={'pk': self.payout.id})

        for remote_status, local_status in statuses:
            data = json.dumps({
                'data': {
                    'id': self.payout.id,
                    'type': 'funding/payouts',
                    'attributes': {
                        'status': remote_status
                    }
                }
            })
            response = self.client.put(
                payout_url, data,
                HTTP_AUTHORIZATION="Token {}".format(self.token))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.payout.refresh_from_db()
            self.assertEqual(self.payout.status, local_status)

    def test_payouts_api_payout_date(self):
        """
        Update payout status
        """
        payout_url = reverse('payout-details', kwargs={'pk': self.payout.id})

        data = json.dumps({
            'data': {
                'id': self.payout.id,
                'type': 'funding/payouts',
                'attributes': {
                    'status': 'scheduled'
                }
            }
        })

        response = self.client.put(
            payout_url, data,
            HTTP_AUTHORIZATION="Token {}".format(self.token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'scheduled')
        self.assertIsNone(self.payout.date_completed)

        data = json.dumps({
            'data': {
                'id': self.payout.id,
                'type': 'funding/payouts',
                'attributes': {
                    'status': 'success'
                }
            }
        })

        response = self.client.put(
            payout_url, data,
            HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'succeeded')
        self.assertIsNotNone(self.payout.date_completed)

        data = json.dumps({
            'data': {
                'id': self.payout.id,
                'type': 'funding/payouts',
                'attributes': {
                    'status': 're_scheduled'
                }
            }
        })
        response = self.client.put(
            payout_url, data,
            HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'scheduled')
        self.assertIsNone(self.payout.date_completed)


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'api_key': 'sk_test_api_key',
        'webhook_secret': 'whsec_test_webhook_secret',
        'webhook_secret_connect': 'whsec_test_webhook_secret_connect',
    }
]
