from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


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
                'type': 'payout-plain',
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
        # Check that the changes are really persisted
        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_holder_name'], "Henkie Henk")

    def test_create_payout_account(self):
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'payout-plain',
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
                'type': 'payout-plain',
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
