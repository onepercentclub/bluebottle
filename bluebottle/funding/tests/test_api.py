import json
from datetime import timedelta
from io import BytesIO

import mock
import munch
import stripe
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.timezone import now
from moneyed import Money
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.authtoken.models import Token

from bluebottle.funding.models import Donor, FundingPlatformSettings, Funding
from bluebottle.funding.tests.factories import (
    FundingFactory,
    PlainPayoutAccountFactory,
    RewardFactory,
    DonorFactory,
    BudgetLineFactory,
)
from bluebottle.funding.tests.test_admin import generate_mock_bank_account
from bluebottle.funding_flutterwave.tests.factories import (
    FlutterwaveBankAccountFactory, FlutterwavePaymentFactory, FlutterwavePaymentProviderFactory
)
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import (
    LipishaBankAccountFactory, LipishaPaymentFactory, LipishaPaymentProviderFactory
)
from bluebottle.funding_pledge.tests.factories import (
    PledgeBankAccountFactory, PledgePaymentProviderFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.models import StripePaymentProvider
from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory, \
    StripeSourcePaymentFactory, ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.funding_vitepay.models import VitepayPaymentProvider
from bluebottle.funding_vitepay.tests.factories import (
    VitepayBankAccountFactory, VitepayPaymentFactory, VitepayPaymentProviderFactory
)
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase


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
        self.funding_url = reverse('funding-detail', args=(self.funding.pk,))

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

        self.update_url = reverse('funding-budget-line-detail', args=(self.budget_line.pk,))

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
        self.funding_url = reverse('funding-detail', args=(self.funding.pk,))

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

    def test_create_coinitiator(self):
        coinitiator = BlueBottleUserFactory.create()
        self.initiative.activity_managers.add(coinitiator)
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=coinitiator
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

        self.update_url = reverse('funding-reward-detail', args=(self.reward.pk,))

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
            target=Money(5000, "EUR"),
            deadline=now() + timedelta(days=15),
        )

        BudgetLineFactory.create(activity=self.funding)

        self.funding.bank_account = generate_mock_bank_account()
        self.funding.save()
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        self.funding_url = reverse("funding-detail", args=(self.funding.pk,))
        self.data = {
            "data": {
                "id": self.funding.pk,
                "type": "activities/fundings",
                "attributes": {
                    "title": "New title",
                },
            }
        }

    def test_view_funding_owner(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()
        co_financer = BlueBottleUserFactory.create(is_co_financer=True)
        DonorFactory.create(
            user=co_financer,
            amount=Money(200, 'EUR'),
            activity=self.funding,
            status='succeeded')
        DonorFactory.create_batch(
            4,
            amount=Money(200, 'EUR'),
            activity=self.funding,
            status='succeeded')
        DonorFactory.create_batch(
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

        self.assertEqual(
            response.json()['data']['meta']['contributor-count'],
            5
        )

        co_financers = response.json()['data']['relationships']['co-financers']
        self.assertEqual(len(co_financers), 1)

        # Test that geolocation is included too
        geolocation = self.included_by_type(response, 'geolocations')[0]
        self.assertEqual(geolocation['attributes']['locality'], 'Barranquilla')
        self.assertIsNotNone(data['data']['attributes']['supporters-export-url'])

    def test_get_owner_export_disabled(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = False
        initiative_settings.save()
        DonorFactory.create_batch(
            4,
            amount=Money(200, 'EUR'),
            activity=self.funding,
            status='succeeded')
        DonorFactory.create_batch(
            2,
            amount=Money(100, 'EUR'),
            activity=self.funding,
            status='new')
        response = self.client.get(self.funding_url, user=self.funding.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        export_url = data['attributes']['supporters-export-url']
        self.assertIsNone(export_url)

    def test_get_owner_export_enabled(self):
        SegmentTypeFactory.create()
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()
        DonorFactory.create(activity=self.funding, amount=Money(20, 'EUR'), status='new')
        DonorFactory.create(activity=self.funding, user=None, amount=Money(35, 'EUR'), status='succeeded')
        response = self.client.get(self.funding_url, user=self.funding.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        export_url = data['attributes']['supporters-export-url']['url']
        export_response = self.client.get(export_url)
        sheet = load_workbook(filename=BytesIO(export_response.content)).get_active_sheet()
        self.assertEqual(sheet['A1'].value, 'Email')
        self.assertEqual(sheet['B1'].value, 'Name')
        self.assertEqual(sheet['C1'].value, 'Date')
        self.assertEqual(sheet['D1'].value, 'Amount')
        self.assertEqual(sheet['D2'].value, '35.00 €')
        self.assertEqual(sheet['D3'].value, None)

        wrong_signature_response = self.client.get(export_url + '111')
        self.assertEqual(
            wrong_signature_response.status_code, 404
        )

    def test_get_owner_export_weird_title(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()
        self.funding.title = 'This \ is å süper / weird ++ TITŁE $%$%'
        self.funding.save()
        DonorFactory.create(activity=self.funding, amount=Money(20, 'EUR'), status='new')
        DonorFactory.create(activity=self.funding, user=None, amount=Money(35, 'EUR'), status='succeeded')
        response = self.client.get(self.funding_url, user=self.funding.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        export_url = data["attributes"]["supporters-export-url"]["url"]
        export_response = self.client.get(export_url)
        self.assertEqual(export_response.status_code, 200)

    def test_get_bank_account(self):

        self.funding.bank_account = generate_mock_bank_account()

        self.funding.save()

        connect_account = stripe.Account("some-connect-id")
        connect_account.update(
            {
                "country": "NL",
                "external_accounts": stripe.ListObject({"data": [connect_account]}),
            }
        )

        with mock.patch(
                'stripe.Account.retrieve', return_value=connect_account
        ):
            with mock.patch(
                    'stripe.ListObject.retrieve', return_value=connect_account
            ):
                response = self.client.get(self.funding_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_account = response.json()["data"]["relationships"]["bank-account"]["data"]
        self.assertEqual(bank_account["id"], str(self.funding.bank_account.pk))

    def test_get_bank_account_staff(self):
        self.staff = BlueBottleUserFactory.create(is_staff=True)
        self.funding.bank_account = ExternalAccountFactory.create(
            account_id="some-external-account-id",
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id"
            ),
        )
        self.funding.save()

        connect_account = stripe.Account("some-connect-id")
        connect_account.update(
            {
                "country": "NL",
                "external_accounts": stripe.ListObject({"data": [connect_account]}),
            }
        )

        with mock.patch(
                'stripe.Account.retrieve', return_value=connect_account
        ):
            with mock.patch(
                    'stripe.ListObject.retrieve', return_value=connect_account
            ):
                response = self.client.get(self.funding_url, user=self.staff)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_account = response.json()["data"]["relationships"]["bank-account"]["data"]
        self.assertEqual(bank_account["id"], str(self.funding.bank_account.pk))

    def test_other_user(self):
        DonorFactory.create_batch(
            5, amount=Money(200, "EUR"), activity=self.funding, status="succeeded"
        )
        DonorFactory.create_batch(
            2, amount=Money(100, "EUR"), activity=self.funding, status="new"
        )

        self.funding.bank_account = generate_mock_bank_account()
        self.funding.save()
        connect_account = stripe.Account("some-connect-id")
        connect_account.update(
            {
                "country": "NL",
                "external_accounts": stripe.ListObject({"data": [connect_account]}),
            }
        )

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

    def test_recalculate_refund(self):
        self.funding.status = 'succeeded'
        self.funding.save()
        response = self.client.get(self.funding_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()['data']['meta']['transitions']),
            0
        )
        response = self.client.get(self.funding_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]["meta"]["transitions"]), 0)

    def test_update_bank_account(self):
        external_account = generate_mock_bank_account()
        connect_account = stripe.Account("some-connect-id")
        connect_account.update(
            {
                "country": "NL",
                "external_accounts": stripe.ListObject({"data": [connect_account]}),
            }
        )

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

        settings = InitiativePlatformSettings.objects.get()
        settings.activity_types.append('funding')
        settings.save()

        self.bank_account = PledgeBankAccountFactory.create(
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )

        self.create_url = reverse('funding-list')

        self.data = {
            'data': {
                'type': 'activities/fundings',
                'attributes': {
                    'title': 'test',
                    'description': 'Yeah',
                    'target': {'currency': 'EUR', 'amount': 3500},
                    'deadline': str(now() + timedelta(days=30))
                },
                'relationships': {
                    'initiative': {
                        'data': {
                            'type': 'initiatives',
                            'id': self.initiative.pk,
                        },
                    },
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            data['data']['meta']['permissions']['PATCH']
        )
        self.assertTrue(
            self.included_by_type(response, 'geolocations')[0]
        )

    def test_create_other_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=BlueBottleUserFactory.create())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_other_user_open(self):
        self.initiative.is_open = True
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_other_user_open_not_approved(self):
        self.initiative.is_open = True
        self.initiative.save()
        response = self.client.post(
            self.create_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_without_errors(self):
        self.initiative.status = 'approved'
        self.initiative.save()
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        update_url = reverse('funding-detail', args=(data['data']['id'],))
        response = self.client.put(update_url, data, user=self.user)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        funding = Funding.objects.last()
        funding.bank_account = self.bank_account
        funding.save()

        BudgetLineFactory.create_batch(2, activity=funding)

        response = self.client.get(update_url, data, user=self.user)
        data = response.json()

        self.assertEqual(
            len(data['data']['meta']['errors']),
            0
        )
        self.assertEqual(
            len(data['data']['meta']['required']),
            0
        )
        funding.states.submit(save=True)
        funding.states.approve(save=True)
        data['data']['attributes'] = {
            'deadline': now() + timedelta(days=80),
        }
        response = self.client.put(update_url, data, user=self.user)
        data = response.json()
        self.assertEqual(
            data['data']['meta']['errors'][0]['title'],
            'The deadline should not be more then 60 days in the future'
        )


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
        self.funding_url = reverse('funding-detail', args=(self.funding.pk,))

        self.data = {
            'data': {
                'type': 'contributors/donations',
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
        donation = Donor.objects.get(pk=data['data']['id'])
        donation.states.succeed()
        donation.save()

        response = self.client.get(self.funding_url, user=self.user)

        self.assertTrue(response.json()['data']['attributes']['is-follower'])
        self.assertEqual(response.json()['data']['meta']['contributor-count'], 1)

    def test_donate_anonymous(self):
        self.data['data']['attributes']['anonymous'] = True
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['anonymous'], True)
        donation = Donor.objects.get(pk=data['data']['id'])
        self.assertTrue(donation.user, self.user)

        donation.states.succeed()
        donation.save()

        response = self.client.get(self.funding_url, user=self.user)
        self.assertEqual(response.json()['data']['meta']['contributor-count'], 1)

    def test_update(self):
        response = self.client.post(self.create_url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                },
            }
        }

        response = self.client.patch(update_url, json.dumps(patch_data))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))
        patch_data = {
            'data': {
                'type': 'contributors/donations',
                'id': data['data']['id'],
                'attributes': {
                    'client-secret': data['data']['attributes']['client-secret']
                },
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
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 100, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['user']['data']['id'], str(self.user.pk))
        self.assertTrue('client-secret' not in data['data']['attributes'])

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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

        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))
        patch_data = {
            'data': {
                'type': 'contributors/donations',
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
        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                    'client-secret': data['data']['attributes']['client-secret']
                },
            }
        }

        response = self.client.patch(
            update_url,
            json.dumps(patch_data),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 200, 'currency': 'EUR'})

    def test_update_no_user_set_user(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
                'id': data['data']['id'],
                'attributes': {
                    'amount': {'amount': 200, 'currency': 'EUR'},
                    'client-secret': data['data']['attributes']['client-secret']
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
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['amount'], {'amount': 200, 'currency': 'EUR'})
        self.assertEqual(data['data']['relationships']['user']['data']['id'], str(self.user.pk))

    def test_update_no_user_wrong_token(self):
        response = self.client.post(self.create_url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)
        update_url = reverse('funding-donation-detail', args=(data['data']['id'],))

        patch_data = {
            'data': {
                'type': 'contributors/donations',
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
        provider = StripePaymentProviderFactory.create()
        provider.paymentcurrency_set.create(
            code='EUR',
            min_amount=5,
            max_amount=None,
            default1=10,
            default2=20,
            default3=50,
            default4=100,
        )

    def test_currency_settings(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['platform']['currencies'])

        self.assertTrue(
            {
                'provider': 'stripe',
                'providerName': 'Stripe',
                'code': 'EUR',
                'name': 'Euro',
                'symbol': '€',
                'defaultAmounts': [10.00, 20.00, 50.00, 100.00],
                'minAmount': 5.00,
                'maxAmount': None
            } in response.data['platform']['currencies']
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
        return reverse("payout-details", args=(payout.pk,))

    def test_get_stripe_payout(self):
        self.funding.bank_account = generate_mock_bank_account()
        self.funding.save()

        with mock.patch(
            "bluebottle.funding_stripe.models.ExternalAccount.verified",
            new_callable=mock.PropertyMock,
        ) as verified:
            verified.return_value = True
            self.funding.states.submit()
            self.funding.states.approve()

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
                payment=PledgePaymentFactory.create()
            )
            PledgePaymentFactory.create(donation=donation)

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(300, 'USD'),
                payout_amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            with mock.patch('stripe.Source.modify'):
                StripeSourcePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding,
                status='new',
            )
            with mock.patch('stripe.Source.modify'):
                StripeSourcePaymentFactory.create(donation=donation)
            donation.states.fail()
            donation.save()

        self.funding.states.succeed(save=True)

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
                if donation['type'] == 'contributors/donations'
            ),
            1000.0
        )

    def test_get_vitepay_payout(self):
        VitepayPaymentProvider.objects.all().delete()
        VitepayPaymentProviderFactory.create()
        self.funding.bank_account = VitepayBankAccountFactory.create(
            account_name="Test Tester",
            mobile_number="12345",
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            VitepayPaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonorFactory.create(
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
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            LipishaPaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonorFactory.create(
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
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            FlutterwavePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonorFactory.create(
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
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonorFactory.create(
                amount=Money(200, 'EUR'),
                activity=self.funding, status='succeeded',
            )
            PledgePaymentFactory.create(donation=donation)

        for i in range(2):
            donation = DonorFactory.create(
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
            status="verified",
            connect_account=PlainPayoutAccountFactory.create(status="verified"),
        )
        BudgetLineFactory.create(activity=self.funding)

        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for i in range(5):
            donation = DonorFactory.create(
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
        response = self.client.patch(url, data.json(), user=user)
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
        DonorFactory.create(status='succeeded')
        url = reverse('funding-donation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.get(url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class FundingAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()
        owner = BlueBottleUserFactory.create(is_co_financer=True)
        self.initiative = InitiativeFactory.create(status="approved")
        bank_account = generate_mock_bank_account()
        self.activity = FundingFactory.create(
            owner=owner,
            initiative=self.initiative,
            target=Money(500, "EUR"),
            deadline=now() + timedelta(weeks=2),
            bank_account=bank_account,
        )
        BudgetLineFactory.create(activity=self.activity)
        self.activity.bank_account.reviewed = True

        self.activity.states.submit()
        self.activity.states.approve(save=True)

        self.donors = DonorFactory.create_batch(
            5, activity=self.activity
        )
        self.url = reverse('funding-detail', args=(self.activity.pk,))

    def test_get_owner(self):
        self.perform_get(user=self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)


class FundingPlatformSettingsAPITestCase(APITestCase):

    def setUp(self):
        super(FundingPlatformSettingsAPITestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()

    def test_anonymous_donations_setting(self):
        funding_settings = FundingPlatformSettings.load()
        funding_settings.anonymous_donations = True
        funding_settings.allow_anonymous_rewards = True
        funding_settings.matching_name = "Dagobert Duck"
        funding_settings.save()
        response = self.client.get('/api/config', user=self.user)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEquals(
            data['platform']['funding'],
            {
                "allow_anonymous_rewards": True,
                "anonymous_donations": True,
                "matching_name": "Dagobert Duck",
                'public_accounts': False,
                "stripe_publishable_key": "test-pub-key",
            },
        )


class FundingAnonymousDonationsTestCase(APITestCase):

    def setUp(self):
        super(FundingAnonymousDonationsTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()
        donation = DonorFactory.create(
            user=BlueBottleUserFactory.create(),
            status='succeeded'
        )

        self.url = reverse('funding-donation-detail', args=(donation.id,))

    def test_donation(self):
        self.perform_get()
        self.assertTrue('user' in self.response.json()['data']['relationships'])
        self.assertRelationship('user', self.user)

    def test_anonymous_donation(self):
        funding_settings = FundingPlatformSettings.load()
        funding_settings.anonymous_donations = True
        funding_settings.save()
        self.perform_get()
        self.assertFalse('user' in self.response.json()['data']['relationships'])
