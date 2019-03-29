import json
from mock import patch
import os

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import stripe

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import json2obj


MERCHANT_ACCOUNTS = [
    {
        'merchant': 'stripe',
        'currency': 'EUR',
        'secret_key': 'sk_test_secret_key',
        'webhook_secret': 'whsec_test_webhook_secret',
        'webhook_secret_connect': 'whsec_test_webhook_secret_connect',
    }
]

PROJECT_PAYOUT_FEES = {
    'beneath_threshold': 1,
    'fully_funded': 0.05,
    'not_fully_funded': 0.0725
}


@override_settings(MERCHANT_ACCOUNTS=MERCHANT_ACCOUNTS)
class StripePayoutTestApi(BluebottleTestCase):
    def setUp(self):
        super(StripePayoutTestApi, self).setUp()
        self.country = CountryFactory.create()
        self.init_projects()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())
        self.project = ProjectFactory.create(owner=self.owner)
        self.project_manage_url = reverse('project_manage_detail', kwargs={'slug': self.project.slug})

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    @patch('bluebottle.payouts.models.stripe.Account.create')
    def test_stripe_details(self, stripe_create, stripe_retrieve):
        stripe_create.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json').read()
        )
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'stripe',
                'account_token': "ct_1234567890",
                'document_type': "passport",
                'country': 'NL'
            }
        }
        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_id'], "acct_1DhHdvsdvsdBY")
        self.assertEqual(response.data['payout_account']['document_type'], 'passport')
        self.assertEqual(response.data['payout_account']['type'], "stripe")
        self.assertEqual(response.data['payout_account']['country'], "NL")
        self.assertEqual(response.data['payout_account']['fields_needed'], [])

        self.assertEqual(stripe_create.call_count, 1)
        self.assertEqual(stripe_create.call_args[1]['country'], 'NL')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    @patch('bluebottle.payouts.models.stripe.Account.create')
    def test_stripe_details_unverified(self, stripe_create, stripe_retrieve):
        stripe_create.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_unverified.json').read()
        )
        stripe_retrieve.return_value = json2obj(
            open(os.path.dirname(__file__) + '/data/stripe_account_unverified.json').read()
        )
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'stripe',
                'account_token': "ct_1234567890",
                'document_type': "passport",
                'country': 'NL'
            }
        }
        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_id'], "acct_1DhHdvsdvsdBY")
        self.assertEqual(response.data['payout_account']['document_type'], 'passport')
        self.assertEqual(response.data['payout_account']['type'], "stripe")
        self.assertEqual(response.data['payout_account']['country'], "NL")
        self.assertEqual(response.data['payout_account']['fields_needed'], ['legal_entity.verification.document'])

        self.assertEqual(stripe_create.call_count, 1)
        self.assertEqual(stripe_create.call_args[1]['country'], 'NL')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    @patch('bluebottle.payouts.models.stripe.Account.create')
    def test_stripe_details_update_country(self, stripe_create, stripe_retrieve):
        account = stripe.Account(123)
        account.update(json.load(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json')
        ))
        stripe_create.return_value = account
        stripe_retrieve.return_value = account
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'stripe',
                'account_token': "ct_1234567890",
                'document_type': "passport",
                'country': 'NL'
            }
        }
        self.client.put(self.project_manage_url, project_details, token=self.owner_token)

        project_details['payout_account']['country'] = 'DE'
        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(stripe_create.call_count, 2)
        self.assertEqual(stripe_create.call_args[1]['country'], 'DE')

    @patch('bluebottle.payouts.models.stripe.Account.retrieve')
    @patch('bluebottle.payouts.models.stripe.Account.create')
    def test_project_details_update_when_campiagning(self, stripe_create, stripe_retrieve):
        account = stripe.Account(123)
        account.update(json.load(
            open(os.path.dirname(__file__) + '/data/stripe_account_verified.json')
        ))
        stripe_create.return_value = account
        stripe_retrieve.return_value = account
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'stripe',
                'account_token': "ct_1234567890",
                'document_type': "passport",
                'country': 'NL'
            }
        }
        self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.project.refresh_from_db()
        # Make campaign editable
        campaign = ProjectPhase.objects.get(slug='campaign')
        campaign.editable = True
        campaign.save()
        self.project.status = campaign
        self.project.save()

        project_details['pitch'] = 'Nice things'
        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['pitch'], 'Nice things')


class PayoutAccountApiTestCase(BluebottleTestCase):
    """
    Tests for the Payout Account API.
    """
    def setUp(self):
        super(PayoutAccountApiTestCase, self).setUp()
        self.country = CountryFactory.create()
        self.init_projects()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())
        self.not_owner = BlueBottleUserFactory.create()
        self.not_owner_token = "JWT {0}".format(self.not_owner.get_jwt_token())
        self.project = ProjectFactory.create(owner=self.owner)
        self.project_manage_url = reverse('project_manage_detail', kwargs={'slug': self.project.slug})

    def test_update_payout_account(self):
        payout = PlainPayoutAccountFactory.create()
        self.project.payout_account = payout
        self.project.save()

        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'plain',
                'id': payout.id,
                'account_holder_address': "",
                'account_holder_postal_code': "1011TG",
                'account_holder_city': "Amsterdam",
                'account_holder_country': self.country.id,
                'account_holder_name': "Henkie Henk",
                'account_number': "123456789",
                'account_details': "Big Duck Bank",
                'account_bank_country': self.country.id
            }
        }

        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_holder_name'], "Henkie Henk")
        self.assertEqual(response.data['payout_account']['type'], 'plain')
        # Check that the changes are really persisted
        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_holder_name'], "Henkie Henk")

    def test_create_payout_account(self):
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'plain',
                'account_holder_address': "",
                'account_holder_postal_code': "1011TG",
                'account_holder_city': "Amsterdam",
                'account_holder_country': int(self.country.id),
                'account_holder_name': "Frankie Frank",
                'account_number': "123456789",
                'account_details': "Big Duck Bank",
                'account_bank_country': self.country.id
            }
        }

        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_holder_name'], "Frankie Frank")

    def test_create_payout_account_invalid_type(self):
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'little-green-bag',
                'account_holder_address': "",
                'account_holder_postal_code': "1011TG",
                'account_holder_city': "Amsterdam",
                'account_holder_country': self.country.id,
                'account_holder_name': "Bertje Bert",
                'account_number': "123456789",
                'account_details': "Big Duck Bank",
                'account_bank_country': self.country.id
            }
        }

        response = self.client.patch(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['payout_account']['type']), 'Invalid type')

    def test_create_payout_account_with_document(self):
        self.some_photo = './bluebottle/projects/test_images/loading.gif'
        photo_file = open(self.some_photo, mode='rb')
        self.manage_payout_document_url = reverse('manage_payout_document_list')
        response = self.client.post(self.manage_payout_document_url,
                                    {'file': photo_file},
                                    token=self.owner_token,
                                    format='multipart')

        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['file'])
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'plain',
                'document': response.data['id'],
                'account_holder_address': "",
                'account_holder_postal_code': "1011TG",
                'account_holder_city': "Amsterdam",
                'account_holder_country': self.country.id,
                'account_holder_name': "Frankie Frank",
                'account_number': "123456789",
                'account_details': "Big Duck Bank",
                'account_bank_country': self.country.id
            }
        }

        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['payout_account']['document'])
