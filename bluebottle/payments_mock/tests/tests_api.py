from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.payments.models import OrderPayment
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class PaymentMockTests(TestCase):
    """
    Tests for updating and order payment via mock PSP listener. The listener calls the service to fetch the
    appropriate adapter and update the OrderPayment status. It sets the status of the order payment to
    """

    def setUp(self):
        self.order_payment = OrderPaymentFactory.create(status='created', amount=100, payment_method='mockCreditcard')
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

    def api_status(self, status):
        self.assertEqual(self.order_payment.status, 'created')
        self.assertEqual(OrderPayment.objects.count(), 1)

        data = {'order_payment_id': self.order_payment.id, 'status': status}
        response = self.client.post(reverse('payment-service-provider-status-update'), data)

        self.assertEqual(response.status_code, 200)
        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, status)
        self.assertEqual(OrderPayment.objects.count(), 1)

    def test_status_started_update(self):
        self.api_status('started')

    def test_status_authorized_update(self):
        self.api_status('authorized')

    def test_status_settled_update(self):
        self.api_status('settled')

    def test_status_failed_update(self):
        self.api_status('failed')

    def test_status_cancelled_update(self):
        self.api_status('cancelled')

    def test_status_charged_back_update(self):
        self.api_status('charged_back')

    def test_status_refunded_update(self):
        self.api_status('refunded')

    def test_status_unknown_update(self):
        self.api_status('unknown')

    def test_status_unknown_status(self):
        """ Test if the mapping resolves to 'unknown' if it tries to map a status that is not known to the mapper """
        self.assertEqual(self.order_payment.status, 'created')

        data = {'order_payment_id': self.order_payment.id, 'status': 'very_obscure_unknown_status'}
        response = self.client.post(reverse('payment-service-provider-status-update'), data)

        self.assertEqual(response.status_code, 200)
        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, 'unknown')