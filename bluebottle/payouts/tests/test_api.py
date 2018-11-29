from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payouts import PlainPayoutAccountFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class PayoutAccountApiTestCase(BluebottleTestCase):
    """
    Tests for the Payout Account API.
    """
    def setUp(self):
        super(PayoutAccountApiTestCase, self).setUp()
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
                'account_details': "",
                'account_holder_city': "Amsterdam",
                'account_holder_country': "Netherlands",
                'account_holder_name': "Henkie Henk",
                'account_number': "123456789"
            }
        }

        response = self.client.put(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['payout_account']['account_holder_name'], "Henkie Henk")

    def test_create_payout_account(self):
        project_details = {
            'title': self.project.title,
            'payout_account': {
                'type': 'payout-plain',
                'account_details': "",
                'account_holder_city': "Amsterdam",
                'account_holder_country': "Netherlands",
                'account_holder_name': "Frankie Frank",
                'account_number': "123456789"
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
                'account_details': "",
                'account_holder_city': "Amsterdam",
                'account_holder_country': "Netherlands",
                'account_holder_name': "Bertie Bert",
                'account_number': "123456789"
            }
        }

        response = self.client.patch(self.project_manage_url, project_details, token=self.owner_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['payout_account']['type']), 'Invalid type')
