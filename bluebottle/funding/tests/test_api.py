from datetime import timedelta
import json

from moneyed import Money

from django.urls import reverse
from django.utils.timezone import now

from rest_framework import status
from bluebottle.funding.tests.factories import FundingFactory, FundraiserFactory, RewardFactory
from bluebottle.funding.models import Donation
from bluebottle.funding_pledge.models import PledgePaymentProvider
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class BudgetLineListTestCase(BluebottleTestCase):
    def setUp(self):
        super(BudgetLineListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative, accepted_currencies=['EUR'])

        self.create_url = reverse('funding-budget-line-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'activities/budgetlines',
                'attributes': {
                    'description': 'test',
                    'amount': {'amount': 100, 'currency': 'EUR'},
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['description'],
            self.data['data']['attributes']['description']
        )

        response = self.client.get(self.funding_url, user=self.user)
        funding_data = json.loads(response.content)

        self.assertEqual(
            len(funding_data['data']['relationships']['budgetlines']['data']), 1
        )
        self.assertEqual(
            funding_data['data']['relationships']['budgetlines']['data'][0]['id'],
            data['data']['id']
        )

    def test_create_wrong_currency(self):
        self.data['data']['attributes']['amount']['currency'] = 'USD'
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_other_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_no_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RewardListTestCase(BluebottleTestCase):
    def setUp(self):
        super(RewardListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative, accepted_currencies=['EUR'])

        self.create_url = reverse('funding-reward-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'activities/rewards',
                'attributes': {
                    'title': 'Test title',
                    'description': 'Test description',
                    'amount': {'amount': 100, 'currency': 'EUR'},
                    'limit': 10,
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['description'],
            self.data['data']['attributes']['description']
        )
        self.assertEqual(
            data['data']['attributes']['title'],
            self.data['data']['attributes']['title']
        )

        response = self.client.get(self.funding_url)
        funding_data = json.loads(response.content)

        self.assertEqual(
            len(funding_data['data']['relationships']['rewards']['data']), 1
        )
        self.assertEqual(
            funding_data['data']['relationships']['rewards']['data'][0]['id'], unicode(data['data']['id'])
        )

    def test_create_wrong_currency(self):
        self.data['data']['attributes']['amount']['currency'] = 'USD'
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_other_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_no_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FundraiserListTestCase(BluebottleTestCase):
    def setUp(self):
        super(FundraiserListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative, accepted_currencies=['EUR'])

        self.create_url = reverse('funding-fundraiser-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'activities/fundraisers',
                'attributes': {
                    'title': 'Test title',
                    'description': 'Test description',
                    'amount': {'amount': 100, 'currency': 'EUR'},
                    'deadline': str((now() + timedelta(days=10)).date())
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, data=json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['description'],
            self.data['data']['attributes']['description']
        )
        self.assertEqual(
            data['data']['attributes']['title'],
            self.data['data']['attributes']['title']
        )
        self.assertEqual(
            data['data']['relationships']['owner']['data']['id'],
            unicode(self.user.pk)
        )

        response = self.client.get(self.funding_url)
        funding_data = json.loads(response.content)

        self.assertEqual(
            len(funding_data['data']['relationships']['fundraisers']['data']), 1
        )
        self.assertEqual(
            funding_data['data']['relationships']['fundraisers']['data'][0]['id'], data['data']['id']
        )

    def test_create_wrong_currency(self):
        self.data['data']['attributes']['amount']['currency'] = 'USD'
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deadline_to_long(self):
        self.data['data']['attributes']['deadline'] = unicode(self.funding.deadline + timedelta(days=1))
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_other_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_no_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DonationListTestCase(BluebottleTestCase):
    def setUp(self):
        super(DonationListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative, accepted_currencies=['EUR'])

        self.create_url = reverse('funding-donation-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'contributions/donations',
                'attributes': {
                    'amount': {'amount': 100, 'currency': 'EUR'},
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], Donation.Status.new)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['activity']['data']['id'], unicode(self.funding.pk))
        self.assertEqual(data['data']['relationships']['user']['data']['id'], unicode(self.user.pk))

    def test_create_fundraiser(self):
        fundraiser = FundraiserFactory.create(activity=self.funding)
        self.data['data']['relationships']['fundraiser'] = {
            'data': {'id': fundraiser.pk, 'type': 'activities/fundraisers'}
        }

        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['relationships']['fundraiser']['data']['id'], unicode(fundraiser.pk))

    def test_create_fundraiser_unrelated(self):
        fundraiser = FundraiserFactory.create()
        self.data['data']['relationships']['fundraiser'] = {
            'data': {'id': fundraiser.pk, 'type': 'activities/fundraisers'}
        }

        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reward(self):
        reward = RewardFactory.create(amount=Money(100, 'EUR'), activity=self.funding)
        self.data['data']['relationships']['reward'] = {
            'data': {'id': reward.pk, 'type': 'activities/rewards'}
        }
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['relationships']['reward']['data']['id'], unicode(reward.pk))

    def test_create_reward_wrong_amount(self):
        reward = RewardFactory.create(amount=Money(50, 'EUR'), activity=self.funding)
        self.data['data']['relationships']['reward'] = {
            'data': {'id': reward.pk, 'type': 'activities/rewards'}
        }
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reward_wrong_activity(self):
        reward = RewardFactory.create(amount=Money(100, 'EUR'))
        self.data['data']['relationships']['reward'] = {
            'data': {'id': reward.pk, 'type': 'activities/rewards'}
        }
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaymentMethodListTestCase(BluebottleTestCase):
    def setUp(self):
        super(PaymentMethodListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.payment_method_url = reverse('funding-payment-method-list')
        StripePaymentProvider.objects.create(ideal=True, direct_debit=True, bancontact=True)
        PledgePaymentProvider.objects.create()

    def test_list(self):
        response = self.client.get(self.payment_method_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(
            response.data[0]['code'],
            'credit_card'
        )
        self.assertEqual(
            response.data[4]['code'],
            'pledge'
        )
