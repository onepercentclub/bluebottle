from django.test import TestCase
from bluebottle.test.utils import InitProjectDataMixin
from bluebottle.bb_orders.tests.test_api import OrderApiTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundRaiserFactory
from bluebottle.utils.model_dispatcher import get_project_model
from bluebottle.test.utils import BluebottleTestCase


PROJECT_MODEL = get_project_model()


class TestDonationSignals(InitProjectDataMixin, BluebottleTestCase):

	def setUp(self):
		super(TestDonationSignals, self).setUp()

		self.user1 = BlueBottleUserFactory.create()
		#self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.init_projects()
        self.project1.set_status('campaign')
        self.order = OrderFactory.create(user=self.user1)
        self.donation = DonationFactory(order=self.order, amount=35)


	def test_system_wallpost_project_after_donation(self):
		self.assertEqual(SystemWallpost.objects.count(), 0)

		# Set the order to success
        self.order.locked()
        self.order.succeeded()
        self.assertEqual(SystemWallpost.objects.count(), 1)


	def test_system_wallpost_fundraiser_after_donation(self):
		pass