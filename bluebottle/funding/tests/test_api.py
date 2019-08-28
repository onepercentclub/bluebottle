import json
from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from moneyed import Money
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, FundraiserFactory, RewardFactory, DonationFactory
from bluebottle.funding.transitions import DonationTransitions
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class BudgetLineListTestCase(BluebottleTestCase):
    def setUp(self):
        super(BudgetLineListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(
            owner=self.user,
            initiative=self.initiative,
        )

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

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(
            owner=self.user,
            initiative=self.initiative
        )

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


class FundingDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(FundingDetailTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        self.funding = FundingFactory.create(
            initiative=self.initiative,
            deadline=now() + timedelta(days=15)
        )

        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

    def test_view_funding(self):
        DonationFactory.create_batch(3, activity=self.funding, status='succeeded')
        DonationFactory.create_batch(2, activity=self.funding, status='new')

        response = self.client.get(self.funding_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)

        self.assertEqual(
            data['data']['attributes']['description'],
            self.funding.description
        )
        self.assertEqual(
            data['data']['attributes']['title'],
            self.funding.title
        )

        # Should only see the three successful donations
        self.assertEqual(
            len(data['data']['relationships']['contributions']['data']),
            3
        )


class FundraiserListTestCase(BluebottleTestCase):
    def setUp(self):
        super(FundraiserListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        self.funding = FundingFactory.create(
            initiative=self.initiative,
            deadline=now() + timedelta(days=15)
        )

        self.create_url = reverse('funding-fundraiser-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'activities/fundraisers',
                'attributes': {
                    'title': 'Test title',
                    'description': 'Test description',
                    'amount': {'amount': 100, 'currency': 'EUR'},
                    'deadline': str(now() + timedelta(days=10))
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
        # Should be allowed
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_no_user(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FundingTestCase(BluebottleTestCase):
    def setUp(self):
        super(FundingTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create(owner=self.user)

        self.create_url = reverse('funding-list')

        self.data = {
            'data': {
                'type': 'activities/fundings',
                'attributes': {
                    'title': 'test',
                },
                'relationships': {
                    'initiative': {
                        'data': {
                            'type': 'initiatives',
                            'id': self.initiative.pk,
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        data = response.json()

        self.assertTrue(
            data['data']['meta']['permissions']['PATCH']
        )
        self.assertTrue(
            get_included(response, 'geolocations')
        )


class DonationTestCase(BluebottleTestCase):
    def setUp(self):
        super(DonationTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)

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

        self.assertEqual(data['data']['attributes']['status'], DonationTransitions.values.new)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['activity']['data']['id'], unicode(self.funding.pk))
        self.assertEqual(data['data']['relationships']['user']['data']['id'], unicode(self.user.pk))
        self.assertIsNone(data['data']['attributes']['client-secret'])

    def test_update(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['amount'], {'amount': 200, 'currency': 'EUR'})

    def test_update_change_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'relationships': {
                    'user': {
                        'data': {
                            'id': BlueBottleUserFactory.create().pk,
                            'type': 'members',
                        }
                    }
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)

        self.assertEqual(
            data['errors'][0]['detail'],
            u'User can only be set, not changed.'
        )

    def test_update_wrong_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data), user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_no_token(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_no_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], DonationTransitions.values.new)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(len(data['data']['attributes']['client-secret']), 32)
        self.assertEqual(data['data']['relationships']['activity']['data']['id'], unicode(self.funding.pk))
        self.assertEqual(data['data']['relationships']['user']['data'], None)

    def test_update_no_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
            HTTP_AUTHORIZATION='Donation {}'.format(data['data']['attributes']['client-secret'])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 200, 'currency': 'EUR'})

    def test_update_no_user_set_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
                'relationships': {
                    'user': {
                        'data': {
                            'id': self.user.pk,
                            'type': 'members',
                        }
                    }
                }
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
            HTTP_AUTHORIZATION='Donation {}'.format(data['data']['attributes']['client-secret'])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 200, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['user']['data']['id'], unicode(self.user.pk))

    def test_update_no_user_wrong_token(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))

        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
            HTTP_AUTHORIZATION='Donation wrong-token'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
