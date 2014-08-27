from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.payments.models import OrderPayment
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class PaymentMockTests(TestCase):
    def setUp(self):
        self.order_payment = OrderPaymentFactory.create(status='created', amount=100, payment_method='mockCreditcard')
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

    def test_status_success_update(self):
        self.assertEqual(self.order_payment.status, 'created')

        data = {'order_payment_id': self.order_payment.id, 'status': 'settled'}
        response = self.client.post(reverse('payment-service-provider-status-update'),
                                    data)#,
                                #/HTTP_AUTHORIZATION=self.user1_token)

        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, 'settled')