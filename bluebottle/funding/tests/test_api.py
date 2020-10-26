from builtins import str
from builtins import range
import json
from datetime import timedelta
import mock
import munch

import stripe

from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.timezone import now
from moneyed import Money
from rest_framework import status
from rest_framework.authtoken.models import Token

from bluebottle.funding.tests.factories import (
    FundingFactory, RewardFactory, DonationFactory,
    BudgetLineFactory
)
from bluebottle.funding.models import Donation
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_pledge.tests.factories import (
    PledgeBankAccountFactory, PledgePaymentProviderFactory
)
from bluebottle.funding_lipisha.tests.factories import (
    LipishaBankAccountFactory, LipishaPaymentFactory, LipishaPaymentProviderFactory
)
from bluebottle.funding_flutterwave.tests.factories import (
    FlutterwaveBankAccountFactory, FlutterwavePaymentFactory, FlutterwavePaymentProviderFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePaymentProviderFactory, \
    StripePayoutAccountFactory, StripeSourcePaymentFactory
from bluebottle.funding_vitepay.models import VitepayPaymentProvider
from bluebottle.funding_vitepay.tests.factories import (
    VitepayBankAccountFactory, VitepayPaymentFactory, VitepayPaymentProviderFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class BudgetLineListTestCase(BluebottleTestCase):
    def setUp(self):
        super(BudgetLineListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(
            owner=self.user,
            initiative=self.initiative,
        )

        self.create_url = reverse('funding-budget-line-list')
        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))

        self.data = {
            'data': {
                'type': 'activities/budget-lines',
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
            len(funding_data['data']['relationships']['budget-lines']['data']), 1
        )
        self.assertEqual(
            funding_data['data']['relationships']['budget-lines']['data'][0]['id'],
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


class BudgetLineDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(BudgetLineDetailTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(
            owner=self.user,
            initiative=self.initiative
        )
        self.budget_line = BudgetLineFactory.create(activity=self.funding)

        self.update_url = reverse('funding-budget-line-detail', args=(self.budget_line.pk, ))

        self.data = {
            'data': {
                'type': 'activities/budget-lines',
                'id': self.budget_line.pk,
                'attributes': {
                    'description': 'Some other title',
                },
            }
        }

    def test_update(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data),
            user=self.funding.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.budget_line.refresh_from_db()

        self.assertEqual(
            self.budget_line.description,
            self.data['data']['attributes']['description']
        )

    def test_update_anonymous(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_other_user(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_anonymous(self):
        response = self.client.get(
            self.update_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user(self):
        response = self.client.get(
            self.update_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RewardListTestCase(BluebottleTestCase):
    def setUp(self):
        super(RewardListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

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
            funding_data['data']['relationships']['rewards']['data'][0]['id'], str(data['data']['id'])
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


class RewardDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(RewardDetailTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(
            owner=self.user,
            initiative=self.initiative
        )
        self.reward = RewardFactory.create(activity=self.funding)

        self.update_url = reverse('funding-reward-detail', args=(self.reward.pk, ))

        self.data = {
            'data': {
                'type': 'activities/rewards',
                'id': self.reward.pk,
                'attributes': {
                    'title': 'Some other title',
                },
            }
        }

    def test_update(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data),
            user=self.funding.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reward.refresh_from_db()

        self.assertEqual(
            self.reward.title,
            self.data['data']['attributes']['title']
        )

    def test_update_anonymous(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data)
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_other_user(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_anonymous(self):
        response = self.client.get(
            self.update_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user(self):
        response = self.client.get(
            self.update_url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FundingDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(FundingDetailTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.geolocation = GeolocationFactory.create(locality='Barranquilla')
        self.initiative = InitiativeFactory.create(
            owner=self.user,
            place=self.geolocation
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(
            initiative=self.initiative,
            owner=self.user,
            target=Money(5000, 'EUR'),
            deadline=now() + timedelta(days=15)
        )

        BudgetLineFactory.create(activity=self.funding)

        self.funding.bank_account = ExternalAccountFactory.create(
            account_id='some-external-account-id',
            status='verified'
        )
        self.funding.save()
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        self.funding_url = reverse('funding-detail', args=(self.funding.pk, ))
        self.data = {
            'data': {
                'id': self.funding.pk,
                'type': 'activities/fundings',
                'attributes': {
                    'title': 'New title',
                }
            }
        }

    def test_view_funding_owner(self):
        co_financer = BlueBottleUserFactory.create(is_co_financer=True)
        DonationFactory.create(
            user=co_financer,
            amount=Money(200, 'EUR'),
            activity=self.funding,
            status='succeeded')
        DonationFactory.create_batch(
            4,
            amount=Money(200, 'EUR'),
            activity=self.funding,
            status='succeeded')
        DonationFactory.create_batch(
            2,
            amount=Money(100, 'EUR'),
            activity=self.funding,
            status='new')

        self.funding.amount_matching = Money(500, 'EUR')
        self.funding.save()

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
        self.assertEqual(
            data['data']['attributes']['target'],
            {u'currency': u'EUR', u'amount': 5000.0}
        )
        self.assertEqual(
            data['data']['attributes']['amount-donated'],
            {u'currency': u'EUR', u'amount': 1000.0}
        )
        self.assertEqual(
            data['data']['attributes']['amount-matching'],
            {u'currency': u'EUR', u'amount': 500.0}
        )
        self.assertEqual(
            data['data']['attributes']['amount-raised'],
            {u'currency': u'EUR', u'amount': 1500.0}
        )

        # Should only see the three successful donations
        self.assertEqual(
            len(data['data']['relationships']['contributions']['data']),
            5
        )

        # There should be a co-financer in the includes
        included = response.json()['included']
        co_financers = [
            inc for inc in included if inc['type'] == 'members' and inc['attributes']['is-co-financer']
        ]
        self.assertEqual(len(co_financers), 1)

        # Test that geolocation is included too
        geolocation = get_included(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['locality'], 'Barranquilla')

        export_url = data['data']['attributes']['supporters-export-url']['url']

        export_response = self.client.get(export_url)
        self.assertTrue(b'Email,Name,Donation Date' in export_response.content)

        wrong_signature_response = self.client.get(export_url + '111')
        self.assertEqual(
            wrong_signature_response.status_code, 404
        )

    def test_get_bank_account(self):
        self.funding.bank_account = ExternalAccountFactory.create(
            account_id='some-external-account-id',
            status='verified'
        )
        self.funding.save()

        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': 'NL',
            'external_accounts': stripe.ListObject({
                'data': [connect_account]
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=connect_account
        ):
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=connect_account
            ):
                response = self.client.get(self.funding_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_account = response.json()['data']['relationships']['bank-account']['data']
        self.assertEqual(
            bank_account['id'], str(self.funding.bank_account.pk)
        )

    def test_other_user(self):
        DonationFactory.create_batch(5, amount=Money(200, 'EUR'), activity=self.funding, status='succeeded')
        DonationFactory.create_batch(2, amount=Money(100, 'EUR'), activity=self.funding, status='new')

        self.funding.bank_account = ExternalAccountFactory.create(
            account_id='some-external-account-id',
            status='verified'
        )
        self.funding.save()
        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': 'NL',
            'external_accounts': stripe.ListObject({
                'data': [connect_account]
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=connect_account
        ):
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=connect_account
            ):
                response = self.client.get(self.funding_url, user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('bank_account' not in response.json()['data']['relationships'])
        self.assertIsNone(response.json()['data']['attributes']['supporters-export-url'])

    def test_update(self):
        response = self.client.patch(
            self.funding_url,
            data=json.dumps(self.data),
            user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['attributes']['title'],
            'New title'
        )

    def test_update_bank_account(self):
        external_account = ExternalAccountFactory.create(
            account_id='some-external-account-id',
            status='verified'
        )
        connect_account = stripe.Account('some-connect-id')
        connect_account.update({
            'country': 'NL',
            'external_accounts': stripe.ListObject({
                'data': [connect_account]
            })
        })

        with mock.patch(
            'stripe.Account.retrieve', return_value=connect_account
        ):
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=connect_account
            ):
                response = self.client.patch(
                    self.funding_url,
                    data=json.dumps({
                        'data': {
                            'id': self.funding.pk,
                            'type': 'activities/fundings',
                            'relationships': {
                                'bank_account': {
                                    'data': {
                                        'id': external_account.pk,
                                        'type': 'payout-accounts/stripe-external-accounts'
                                    }
                                }
                            }
                        }
                    }),
                    user=self.user
                )
        self.assertEqual(response.status_code, 200)

        bank_account = response.json()['data']['relationships']['bank-account']['data']
        self.assertEqual(
            bank_account['id'], str(external_account.pk)
        )
        self.assertEqual(
            bank_account['type'], 'payout-accounts/stripe-external-accounts'
        )

    def test_update_unauthenticated(self):
        response = self.client.put(self.funding_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_wrong_user(self):
        response = self.client.put(
            self.funding_url, json.dumps(self.data), user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cancelled(self):
        self.funding.states.cancel(save=True)
        response = self.client.put(self.funding_url, json.dumps(self.data), user=self.funding.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deleted(self):
        self.funding = FundingFactory.create()
        self.funding.states.delete(save=True)
        response = self.client.put(self.funding_url, json.dumps(self.data), user=self.funding.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_rejected(self):
        self.funding = FundingFactory.create()
        self.funding.states.reject(save=True)
        response = self.client.put(self.funding_url, json.dumps(self.data), user=self.funding.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(
            data['data']['meta']['permissions']['PATCH']
        )
        self.assertTrue(
            get_included(response, 'geolocations')
        )

    def test_create_other_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=BlueBottleUserFactory.create())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DonationTestCase(BluebottleTestCase):
    def setUp(self):
        super(DonationTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

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

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['activity']['data']['id'], str(self.funding.pk))
        self.assertEqual(data['data']['relationships']['user']['data']['id'], str(self.user.pk))
        self.assertIsNone(data['data']['attributes']['client-secret'])

    def test_donate(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        donation = Donation.objects.get(pk=data['data']['id'])
        donation.states.succeed()
        donation.save()

        response = self.client.get(self.funding_url, user=self.user)

        donation = get_included(response, 'contributions/donations')
        self.assertEqual(donation['relationships']['user']['data']['id'], str(self.user.pk))

        self.assertTrue(response.json()['data']['attributes']['is-follower'])

    def test_donate_anonymous(self):
        self.data['data']['attributes']['anonymous'] = True
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['anonymous'], True)
        donation = Donation.objects.get(pk=data['data']['id'])
        self.assertTrue(donation.user, self.user)

        donation.states.succeed()
        donation.save()

        response = self.client.get(self.funding_url, user=self.user)

        donation = get_included(response, 'contributions/donations')
        self.assertFalse('user' in donation['relationships'])

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

    def test_update_set_donor_name(self):
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
                    'name': 'Pietje'
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['name'], 'Pietje')

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

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(len(data['data']['attributes']['client-secret']), 32)
        self.assertEqual(data['data']['relationships']['activity']['data']['id'], str(self.funding.pk))
        self.assertEqual(data['data']['relationships']['user']['data'], None)

    def test_claim(self):
        response = self.client.post(self.create_url, json.dumps(self.data))
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))
        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'relationships': {
                    'user': {
                        'data': {
                            'id': self.user.pk,
                            'type': 'members',
                        }
                    }
                },
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
            HTTP_AUTHORIZATION='Donation {}'.format(data['data']['attributes']['client-secret'])
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['user']['data']['id'], str(self.user.pk))
        self.assertTrue('client-secret' not in data['data']['attributes'])

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
            user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_claim_authorized(self):
        response = self.client.post(self.create_url, json.dumps(self.data))
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'], ))
        patch_data = {
            'data': {
                'type': 'contributions/donations',
                'id': data['data']['id'],
                'relationships': {
                    'user': {
                        'data': {
                            'id': self.user.pk,
                            'type': 'members',
                        }
                    }
                },
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
            user=self.user
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
        self.assertEqual(data['data']['relationships']['user']['data']['id'], str(self.user.pk))

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

    def test_create_reward(self):
        reward = RewardFactory.create(amount=Money(100, 'EUR'), activity=self.funding)
        self.data['data']['relationships']['reward'] = {
            'data': {'id': reward.pk, 'type': 'activities/rewards'}
        }
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['relationships']['reward']['data']['id'], str(reward.pk))

    def test_create_reward_higher_amount(self):
        reward = RewardFactory.create(amount=Money(50, 'EUR'), activity=self.funding)
        self.data['data']['relationships']['reward'] = {
            'data': {'id': reward.pk, 'type': 'activities/rewards'}
        }
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['relationships']['reward']['data']['id'], str(reward.pk))

    def test_create_reward_lower_amount(self):
        reward = RewardFactory.create(amount=Money(150, 'EUR'), activity=self.funding)
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


class CurrencySettingsTestCase(BluebottleTestCase):
    def setUp(self):
        super(CurrencySettingsTestCase, self).setUp()
        self.settings_url = reverse('settings')
        stripe = StripePaymentProviderFactory.create()
        stripe.paymentcurrency_set.filter(code__in=['AUD', 'GBP']).all().delete()
        flutterwave_provider = FlutterwavePaymentProviderFactory.create()

        cur = flutterwave_provider.paymentcurrency_set.first()
        cur.min_amount = 1000
        cur.default1 = 1000
        cur.default2 = 2000
        cur.default3 = 5000
        cur.default4 = 10000
        cur.save()

    def test_currency_settings(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data['platform']['currencies'],
            [
                {
                    'code': 'EUR',
                    'name': 'Euro',
                    'maxAmount': None,
                    'symbol': u'\u20ac',
                    'minAmount': 5.00,
                    'defaultAmounts': [10.00, 20.00, 50.00, 100.00],
                    'provider': 'stripe'
                },
                {
                    'code': 'USD',
                    'name': 'US Dollar',
                    'maxAmount': None,
                    'symbol': '$',
                    'minAmount': 5.00,
                    'defaultAmounts': [10.00, 20.00, 50.00, 100.00],
                    'provider': 'stripe'
                },
                {
                    'code': 'NGN',
                    'name': 'Nigerian Naira',
                    'maxAmount': None,
                    'symbol': u'\u20a6',
                    'minAmount': 1000.00,
                    'defaultAmounts': [1000.00, 2000.00, 5000.00, 10000.00],
                    'provider': 'flutterwave'
                }
            ]
        )


class PayoutAccountTestCase(BluebottleTestCase):
    def setUp(self):
        super(PayoutAccountTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        self.stripe = StripePaymentProviderFactory.create()
        flutterwave_provider = FlutterwavePaymentProviderFactory.create()
        cur = flutterwave_provider.paymentcurrency_set.first()
        cur.min_amount = 1000
        cur.default1 = 1000
        cur.default2 = 2000
        cur.default3 = 5000
        cur.default4 = 10000
        cur.save()
        self.stripe_account = StripePayoutAccountFactory.create()
        self.stripe_bank = ExternalAccountFactory.create(connect_account=self.stripe_account, status='verified')

        self.funding = FundingFactory.create(
            bank_account=self.stripe_bank,
            target=Money(5000, 'EUR'),
            status='open'
        )
        self.funding_url = reverse('funding-detail', args=(self.funding.id,))
        self.connect_account = stripe.Account('some-connect-id')

        self.connect_account.update({
            'country': 'NL',
            'external_accounts': stripe.ListObject({
                'data': [self.connect_account]
            })
        })

    def test_stripe_methods(self):
        self.stripe.paymentcurrency_set.filter(code__in=['AUD', 'GBP']).all().delete()
        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=self.connect_account
            ):
                response = self.client.get(self.funding_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        included = json.loads(response.content)['included']

        payment_methods = [method['attributes'] for method in included if method['type'] == u'payments/payment-methods']

        self.assertEqual(
            payment_methods,
            [
                {
                    u'code': u'bancontact',
                    u'name': u'Bancontact',
                    u'provider': u'stripe',
                    u'currencies': [u'EUR'],
                    u'countries': [u'BE']
                },
                {
                    u'code': u'credit-card',
                    u'name': u'Credit card',
                    u'provider': u'stripe',
                    u'currencies': [u'EUR', u'USD'],
                    u'countries': []
                },
                {
                    u'code': u'direct-debit',
                    u'name': u'Direct debit',
                    u'provider': u'stripe',
                    u'currencies': [u'EUR'],
                    u'countries': []
                },
                {
                    u'code': u'ideal',
                    u'name': u'iDEAL',
                    u'provider': u'stripe',
                    u'currencies': [u'EUR'],
                    u'countries': [u'NL']
                }
            ]
        )

    def test_stripe_just_credit_card(self):
        self.stripe.ideal = False
        self.stripe.direct_debit = False
        self.stripe.bancontact = False
        self.stripe.save()

        with mock.patch(
            'stripe.Account.retrieve', return_value=self.connect_account
        ):
            with mock.patch(
                'stripe.ListObject.retrieve', return_value=self.connect_account
            ):
                response = self.client.get(self.funding_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        included = json.loads(response.content)['included']

        payment_methods = [method['attributes'] for method in included if method['type'] == u'payments/payment-methods']

        self.assertEqual(
            payment_methods,
            [
                {
                    u'code': u'credit-card',
                    u'name': u'Credit card',
                    u'currencies': [u'EUR', u'USD', u'GBP', u'AUD'],
                    u'provider': u'stripe',
                    u'countries': []
                }
            ]
        )


class PayoutDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(PayoutDetailTestCase, self).setUp()
        StripePaymentProvider.objects.all().delete()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.token = Token.objects.create(user=self.user)

        self.user.groups.add(Group.objects.get(name='Financial'))
        self.geolocation = GeolocationFactory.create(locality='Barranquilla')
        self.initiative = InitiativeFactory.create(
            place=self.geolocation
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR'),
            deadline=now() + timedelta(days=15)
        )
        BudgetLineFactory.create(activity=self.funding)

    def get_payout_url(self, payout):
        return reverse('payout-details', args=(payout.pk, ))

    def test_get_stripe_payout(self):
        self.funding.bank_account = ExternalAccountFactory.create(
            account_id='some-external-account-id',
            status='verified'
        )
        self.funding.save()

        with mock.patch(
            'bluebottle.funding_stripe.models.ExternalAccount.verified', new_callable=mock.PropertyMock
        ) as verified:
            verified.return_value = True
            self.funding.states.submit()
            self.funding.states.approve()

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
                payment=PledgePaymentFactory.create()
            )
            PledgePaymentFactory.create(donation=donation)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(300, 'USD'),
                payout_amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            with mock.patch('stripe.Source.modify'):
                StripeSourcePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            with mock.patch('stripe.Source.modify'):
                StripeSourcePaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed()
        self.funding.save()

        with mock.patch(
            'bluebottle.funding_stripe.models.ExternalAccount.account', new_callable=mock.PropertyMock
        ) as account:
            external_account = stripe.BankAccount('some-bank-token')
            external_account.update(munch.munchify({
                'object': 'bank_account',
                'account_holder_name': 'Jane Austen',
                'account_holder_type': 'individual',
                'bank_name': 'STRIPE TEST BANK',
                'country': 'US',
                'currency': 'usd',
                'fingerprint': '1JWtPxqbdX5Gamtc',
                'last4': '6789',
                'metadata': {
                    'order_id': '6735'
                },
                'routing_number': '110000000',
                'status': 'new',
                'account': 'acct_1032D82eZvKYlo2C'
            }))
            account.return_value = external_account

            response = self.client.get(
                self.get_payout_url(self.funding.payouts.first()),
                HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['data']['id'], str(self.funding.payouts.first().pk))

        self.assertEqual(len(data['data']['relationships']['donations']['data']), 5)
        self.assertEqual(
            sum(
                donation['attributes']['amount']['amount']
                for donation in data['included']
                if donation['type'] == 'contributions/donations'
            ),
            1000.0
        )

    def test_get_vitepay_payout(self):
        VitepayPaymentProvider.objects.all().delete()
        VitepayPaymentProviderFactory.create()
        self.funding.bank_account = VitepayBankAccountFactory.create(
            account_name='Test Tester',
            mobile_number='12345',
            status='verified'
        )
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            VitepayPaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            VitepayPaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed()
        self.funding.save()

        response = self.client.get(
            self.get_payout_url(self.funding.payouts.first()),
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['data']['id'], str(self.funding.payouts.first().pk))

        self.assertEqual(len(data['data']['relationships']['donations']['data']), 5)

    def test_get_lipisha_payout(self):
        LipishaPaymentProvider.objects.all().delete()
        LipishaPaymentProviderFactory.create()
        self.funding.bank_account = LipishaBankAccountFactory.create(
            status='verified'
        )
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            LipishaPaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            LipishaPaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed()
        self.funding.save()

        response = self.client.get(
            self.get_payout_url(self.funding.payouts.first()),
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['data']['id'], str(self.funding.payouts.first().pk))

        self.assertEqual(len(data['data']['relationships']['donations']['data']), 5)

    def test_get_flutterwave_payout(self):
        FlutterwavePaymentProviderFactory.create()
        self.funding.bank_account = FlutterwaveBankAccountFactory.create(
            status='verified'
        )

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            FlutterwavePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            FlutterwavePaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed()
        self.funding.save()

        response = self.client.get(
            self.get_payout_url(self.funding.payouts.first()),
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['data']['id'], str(self.funding.payouts.first().pk))

        self.assertEqual(len(data['data']['relationships']['donations']['data']), 5)

    def test_get_pledge_payout(self):
        PledgePaymentProviderFactory.create()
        self.funding.bank_account = PledgeBankAccountFactory.create(
            status='verified'
        )

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            PledgePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            PledgePaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed()
        self.funding.save()

        response = self.client.get(
            self.get_payout_url(self.funding.payouts.first()),
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['data']['id'], str(self.funding.payouts.first().pk))

        self.assertEqual(len(data['data']['relationships']['donations']['data']), 5)

    def test_put(self):
        PledgePaymentProviderFactory.create()
        self.funding.bank_account = PledgeBankAccountFactory.create(
            status='verified'
        )
        BudgetLineFactory.create(activity=self.funding)

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonationFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            PledgePaymentFactory.create(donation=donation)

        self.funding.states.succeed()
        self.funding.save()

        payout = self.funding.payouts.first()

        response = self.client.put(
            self.get_payout_url(payout),
            data=json.dumps({
                'data': {
                    'id': payout.pk,
                    'type': 'funding/payouts',
                    'attributes': {
                        'status': 'scheduled'
                    }
                }
            }),
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payout.refresh_from_db()
        self.assertEqual(payout.status, 'scheduled')


class FundingAPIPermissionsTestCase(BluebottleTestCase):

    def setUp(self):
        super(FundingAPIPermissionsTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

    def assertPostNotAllowed(self, url, user=None):
        data = self.client.get(url, user=user)
        response = self.client.patch(url, data.data, user=user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_funding_detail(self):
        funding = FundingFactory.create()
        url = reverse('funding-detail', args=(funding.id,))
        self.assertPostNotAllowed(url, self.user)

    def test_funding_budgetline_list(self):
        BudgetLineFactory.create()
        url = reverse('funding-budget-line-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.get(url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_funding_budgetline_detail(self):
        budget_line = BudgetLineFactory.create()
        url = reverse('funding-budget-line-detail', args=(budget_line.id,))
        self.assertPostNotAllowed(url, self.user)

    def test_funding_reward_list(self):
        url = reverse('funding-reward-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.get(url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_funding_reward_detail(self):
        reward = RewardFactory.create()
        url = reverse('funding-reward-detail', args=(reward.id,))
        self.assertPostNotAllowed(url, self.user)

    def test_donation_list(self):
        DonationFactory.create(status='succeeded')
        url = reverse('funding-donation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.get(url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
