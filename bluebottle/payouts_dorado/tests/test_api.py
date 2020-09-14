import json
import os
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils.timezone import now
from mock import patch
from moneyed import Money
from rest_framework import status
from rest_framework.authtoken.models import Token

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory, ExternalAccountFactory, \
    StripePaymentFactory, StripePayoutAccountFactory
from bluebottle.funding_vitepay.tests.factories import VitepayBankAccountFactory
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.utils.utils import json2obj


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

        yesterday = now() - timedelta(days=1)
        payout_account = StripePayoutAccountFactory.create(status='verified')
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account)

        self.funding = FundingFactory.create(
            deadline=yesterday,
            status='open'
        )

        self.funding.bank_account = self.bank_account
        self.funding.save()

        donations = DonationFactory.create_batch(
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
        self.assertEqual(self.payout.status, 'scheduled')
        self.assertIsNone(self.payout.completed)

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

        self.assertEqual(self.payout.status, 'succeeded')
        self.assertIsNotNone(self.payout.paid)

        response = self.client.put(
            payout_url, {'status': 're_scheduled'},
            HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 're_scheduled')
        project = Project.objects.get(pk=self.project.id)
        self.assertEqual(project.payout_status, 're_scheduled')
        self.assertIsNone(project.campaign_paid_out)


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'api_key': 'sk_test_api_key',
        'webhook_secret': 'whsec_test_webhook_secret',
        'webhook_secret_connect': 'whsec_test_webhook_secret_connect',
    }
]


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class TestPayoutProjectApi(BluebottleTestCase):
    """
    Test Project Details in Payouts API
    """

    def setUp(self):
        super(TestPayoutProjectApi, self).setUp()
        self.client = JSONAPITestClient()
        self.init_projects()
        complete = ProjectPhase.objects.get(slug='done-complete')
        incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(self.another_user.get_jwt_token())

        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user)

        bank_vitepay = VitepayBankAccountFactory(
            account_name='Test Tester',
            mobile_number='123456'
        )

        self.funding1 = FundingFactory.create(
            campaign_ended=now(),
            status=complete,
            payout_account=bank_vitepay
        )

        bank_stripe = ExternalAccountFactory(
            account_id='ba_123456'
        )

        self.funding2 = FundingFactory.create(
            campaign_ended=now(),
            status=incomplete,
            payout_account=bank_stripe
        )

    def test_payouts_api_no_token(self):
        """
        """
        payout_url = reverse('payout-detail', kwargs={'pk': self.project1.id})
        response = self.client.get(payout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payouts_api_not_authorized(self):
        """
        """
        payout_url = reverse('payout-detail', kwargs={'pk': self.project1.id})
        response = self.client.get(payout_url, token=self.another_user_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payouts_api_complete_project_details_plain(self):
        """
        """
        payout_url = reverse('payout-detail', kwargs={'pk': self.project1.id})
        response = self.client.get(payout_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['target_reached'], True)
        self.assertEqual(
            response.data['account']['account_holder_name'],
            'Test Tester'
        )
        self.assertEqual(
            response.data['account']['account_number'],
            '123456'
        )
        self.assertEqual(
            response.data['account']['account_bank_country'],
            'Netherlands'
        )

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    def test_payouts_api_complete_project_details_stripe(self, stripe_retrieve):
        """
        """
        StripePaymentProviderFactory.create()
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        payout_url = reverse('payout-detail', kwargs={'pk': self.project2.id})
        response = self.client.get(payout_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['target_reached'], False)

        self.assertEqual(
            response.data['account']['account_id'],
            '123456'
        )


class TestPayoutMethodApi(BluebottleTestCase):
    """
    Test Payout Methods API
    """

    def setUp(self):
        super(TestPayoutMethodApi, self).setUp()
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())
        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user2)
        self.payoutmethods_url = reverse('payout-method-list')

    def test_payoutmethods_api_access_denied_for_anonymous(self):
        """
        """
        response = self.client.get(self.payoutmethods_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payoutmethods_api_access_denied_for_normal_user(self):
        """
        """
        response = self.client.get(self.payoutmethods_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payoutmethods_api_access_granted_for_power_user(self):
        """
        """
        response = self.client.get(self.payoutmethods_url, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['method'], 'duckbank')
