from django.test import TestCase

from bluebottle.test.factory_models.payments import PaymentFactory, OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.models import TestBaseUser


class BlueBottlePaymentTestCase(TestCase):
    
    def setUp(self):
        self.order = OrderFactory.create()
        self.order_payment = OrderPaymentFactory.create(order=self.order)

    def test_basic_order_payment_flow(self):
        self.assertEqual(self.order.status, 'locked')
        self.assertEqual(self.order_payment.status, 'created')

        self.order_payment.started()
        self.assertEqual(self.order.status, 'locked')
        self.assertEqual(self.order_payment.status, 'started')

        self.order_payment.authorized()
        self.assertEqual(self.order.status, 'success')
        self.assertEqual(self.order_payment.status, 'authorized')

        self.order_payment.settled()
        self.assertEqual(self.order.status, 'success')
        self.assertEqual(self.order_payment.status, 'settled')
        