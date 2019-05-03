import unittest

from django.core.urlresolvers import reverse

from bluebottle.payments.models import OrderPayment
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


@unittest.skip("The tests fail because the status of a MockPayment is NULL when saving, triggering an integrity error")
class PaymentMockTests(BluebottleTestCase):
    """
    Tests for updating and order payment via mock PSP listener. The listener calls the service to fetch the
    appropriate adapter and update the OrderPayment status. It sets the status of the order payment to
    """

    def setUp(self):
        super(PaymentMockTests, self).setUp()
        self.init_projects()

        self.order_payment = OrderPaymentFactory.create(
            status=StatusDefinition.CREATED, amount=100, payment_method='mock')
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

    def api_status(self, status):
        self.assertEqual(self.order_payment.status, 'created')
        self.assertEqual(OrderPayment.objects.count(), 1)

        data = {'order_payment_id': self.order_payment.id, 'status': status}
        response = self.client.post(
            reverse('payment-service-provider-status-update'),
            data,
            token=self.user1_token)

        self.assertEqual(response.status_code, 200)
        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, status)
        self.assertEquals(OrderPayment.objects.count(), 1)

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

        data = {'order_payment_id': self.order_payment.id,
                'status': 'very_obscure_unknown_status'}
        response = self.client.post(
            reverse('payment-service-provider-status-update'), data)

        self.assertEqual(response.status_code, 200)
        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, 'unknown')

    def test_update_status_nonexisting_order_payment(self):
        self.assertEqual(self.order_payment.status, 'created')

        data = {'order_payment_id': 5, 'status': 'very_obscure_unknown_status'}
        response = self.client.post(
            reverse('payment-service-provider-status-update'), data)

        self.assertEqual(response.status_code, 404)
        order_payment = OrderPayment.objects.get(id=self.order_payment.id)
        self.assertEquals(order_payment.status, 'created')


class PaymentErrorTests(BluebottleTestCase):
    def setUp(self):
        super(PaymentErrorTests, self).setUp()
        self.init_projects()

        self.donation1 = DonationFactory.create(amount=500)
        self.donation2 = DonationFactory.create(amount=700)
        self.donation3 = DonationFactory.create(amount=5)

        self.user1 = self.donation1.order.user
        self.user1.first_name = 'Jimmy 1%'
        self.user1.save()

        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = self.donation2.order.user
        self.user2.last_name = "Veryveryveryveryveryveryveryveryveryveryveryveryveryveryveryveryveryverylongname"
        self.user2.save()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.order_payment_url = reverse('manage-order-payment-list')

    def test_no_payment_method(self):
        data = {'order': self.donation1.order.id,
                'payment_method': '',
                'integration_data': {'issuerId': 'huey'}
                }

        response = self.client.post(self.order_payment_url, data,
                                    token=self.user1_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['payment_method'][0],
                         u'This field may not be blank.')

    def test_illegal_first_name(self):
        data = {'order': self.donation1.order.id,
                'payment_method': 'mockIdeal',
                'integration_data': {'issuerId': 'huey'}
                }

        response = self.client.post(self.order_payment_url, data,
                                    token=self.user1_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'][0:10], 'First name')

    def test_last_name_too_long(self):
        data = {'order': self.donation2.order.id,
                'payment_method': 'mockIdeal',
                'integration_data': {'issuerId': 'huey'}
                }

        response = self.client.post(self.order_payment_url, data,
                                    token=self.user2_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'][0:9], 'Last name')

    def test_amount_too_low(self):
        user3 = self.donation3.order.user
        user3_token = "JWT {0}".format(user3.get_jwt_token())

        data = {'order': self.donation3.order.id,
                'payment_method': 'mockIdeal',
                'integration_data': {'issuerId': 'huey'}
                }

        response = self.client.post(self.order_payment_url, data,
                                    token=user3_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'][0:6], 'Amount')
