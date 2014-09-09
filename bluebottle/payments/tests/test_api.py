import json
from mock import patch

from django.test import TestCase

from bluebottle.bb_orders.views import ManageOrderDetail
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.test.factory_models.fundraisers import FundRaiserFactory
from bluebottle.test.utils import InitProjectDataMixin

from django.core.urlresolvers import reverse

from rest_framework import status

ORDER_MODEL = get_order_model()


class PaymentApiTestCase(InitProjectDataMixin, TestCase):

    def setUp(self):
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.init_projects()
        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.project1.set_status('campaign')

    def test_payment_errors(self):
        self.order1 = OrderFactory.create(total=0.50, user=self.user1)

