from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import InitProjectDataMixin
from django.core.urlresolvers import reverse
from django.test import TestCase


class ProjectEndpointTestCase(InitProjectDataMixin, TestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.init_projects()
        self.project = ProjectFactory.create(amount_asked=5000)
        self.project.set_status('campaign')

        self.manage_order_list_url = reverse('manage-order-list')
        self.manage_donation_list_url = reverse('manage-donation-list')

    def test_create_donation(self):
        # Check that there's no orders
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.data['count'], 0)
