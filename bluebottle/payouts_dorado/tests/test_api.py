from django.test import override_settings
from mock import patch
import os

from bluebottle.projects.models import Project
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payouts import (
    StripePayoutAccountFactory, PlainPayoutAccountFactory
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import json2obj


class TestPayoutApi(BluebottleTestCase):
    """
    Test Payouts API
    """

    def setUp(self):
        super(TestPayoutApi, self).setUp()
        self.init_projects()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user2)

        self.project = ProjectFactory.create(
            status=ProjectPhase.objects.get(slug='campaign'),
            campaign_ended=now(),
            amount_asked=100)
        donation = DonationFactory.create(
            project=self.project,
            amount=100
        )
        donation.save()
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()
        self.project.save()
        self.project.deadline_reached()

        self.payout_url = reverse('project-payout-detail', kwargs={'pk': self.project.id})

    def test_payouts_api_access_denied_for_anonymous(self):
        """
        """
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payouts_api_access_denied_for_normal_user(self):
        """
        """
        response = self.client.get(self.payout_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payouts_api_access_granted_for_power_user(self):
        """
        """
        response = self.client.get(self.payout_url, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payouts_api_update_payout_status(self):
        """
        Update payout status
        """
        # Possible statuses from Dorado
        statuses = ['needs_approval', 'scheduled', 're_scheduled',
                    'in_progress', 'partial',
                    'success', 'confirmed', 'failed']

        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project.id})

        for st in statuses:
            response = self.client.put(payout_url, {'status': st}, token=self.user2_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], st)
            project = Project.objects.get(pk=self.project.id)
            self.assertEqual(project.payout_status, st)

    def test_payouts_api_payout_date(self):
        """
        Update payout status
        """

        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project.id})

        response = self.client.put(payout_url, {'status': 'scheduled'}, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'scheduled')
        project = Project.objects.get(pk=self.project.id)
        self.assertEqual(project.payout_status, 'scheduled')
        self.assertIsNone(project.campaign_paid_out)

        response = self.client.put(payout_url, {'status': 'success'}, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        project = Project.objects.get(pk=self.project.id)
        self.assertEqual(project.payout_status, 'success')
        self.assertIsNotNone(project.campaign_paid_out)

        response = self.client.put(payout_url, {'status': 're_scheduled'}, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 're_scheduled')
        project = Project.objects.get(pk=self.project.id)
        self.assertEqual(project.payout_status, 're_scheduled')
        self.assertIsNone(project.campaign_paid_out)


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
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
        self.init_projects()
        complete = ProjectPhase.objects.get(slug='done-complete')
        incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(self.another_user.get_jwt_token())

        nl = CountryFactory.create(name='Netherlands')

        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user)

        self.project1 = ProjectFactory.create(
            campaign_ended=now(),
            status=complete,
            payout_account=PlainPayoutAccountFactory(
                account_holder_name='Test Tester',
                account_number='123456',
                account_bank_country=nl,
                account_holder_country=nl
            )
        )
        self.project2 = ProjectFactory.create(
            campaign_ended=now(),
            status=incomplete,
            payout_account=StripePayoutAccountFactory(
                account_id='123456'
            )
        )

    def test_payouts_api_no_token(self):
        """
        """
        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project1.id})
        response = self.client.get(payout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payouts_api_not_authorized(self):
        """
        """
        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project1.id})
        response = self.client.get(payout_url, token=self.another_user_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payouts_api_complete_project_details_plain(self):
        """
        """
        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project1.id})
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
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        payout_url = reverse('project-payout-detail', kwargs={'pk': self.project2.id})
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
