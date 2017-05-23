import json

from moneyed.classes import Money, XOF, EUR
from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.payments.exception import PaymentException
from bluebottle.payments_vitepay.adapters import VitepayPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory

from bluebottle.test.utils import BluebottleTestCase

from .factory_models import VitepayPaymentFactory, VitepayOrderPaymentFactory


vitepay_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'vitepay',
            'currency': 'XOF',
            'api_key': '123',
            'api_secret': '123456789012345678901234567890123456789012345678901234567890',
            'api_url': 'https://api.vitepay.com/v1/prod/payments'
        }
    ]
}


@patch('bluebottle.payments_vitepay.adapters.get_current_host',
       return_value='https://onepercentclub.com')
@override_settings(**vitepay_settings)
class VitepayPaymentAdapterTestCase(BluebottleTestCase):
    def setUp(self):
        super(VitepayPaymentAdapterTestCase, self).setUp()

        self.init_projects()

    def test_create_payment(self, get_current_host):
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(2000, XOF), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='vitepayOrangemoney', order=order)
        adapter = VitepayPaymentAdapter(order_payment)
        self.assertEqual(adapter.payment.amount_100, 200000)

    def test_create_payment_with_wrong_currency(self, get_current_host):
        with self.assertRaises(PaymentException):
            order_payment = OrderPaymentFactory.create(payment_method='vitepayOrangemoney',
                                                       amount=Money(200, EUR))
            VitepayPaymentAdapter(order_payment)

    def test_create_payment_with_wrong_payment_method(self, get_current_host):
        with self.assertRaises(PaymentException):
            order_payment = OrderPaymentFactory.create(payment_method='docdataIdeal',
                                                       amount=Money(3500, XOF))
            adapter = VitepayPaymentAdapter(order_payment)
            adapter.create_payment()

    @patch('bluebottle.payments_vitepay.adapters.VitepayPaymentAdapter._create_payment_hash',
           return_value='123123')
    @patch('bluebottle.payments_vitepay.adapters.requests.post',
           return_value=type('obj', (object,), {'status_code': 200, 'content': 'https://vitepay.com/some-path-to-pay'}))
    def test_authorization_action(self, mock_post, create_hash, get_current_host):
        """
        Play some posts that Vitepay might fire at us.
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(2000, XOF), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='vitepayOrangemoney', order=order)
        adapter = VitepayPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()
        data = {
            u"api_key": u"123",
            u"hash": u"123123",
            u"redirect": 0,
            u"payment": {
                u"description": u"Thanks for your donation!",
                u"order_id": u"opc-{}".format(order_payment.id),
                u"decline_url": u"https://onepercentclub.com/orders/{}/failed".format(order_payment.order.id),
                u"p_type": u"orange_money",
                u"country_code": u"ML",
                u"language_code": u"fr",
                u"amount_100": 200000,
                u"cancel_url": u"https://onepercentclub.com/orders/{}/failed".format(order_payment.order.id),
                u"currency_code": u"XOF",
                u"callback_url": u"https://onepercentclub.com/payments_vitepay/status_update/",
                u"return_url": u"https://onepercentclub.com/orders/{}/success".format(order_payment.order.id)
            }
        }

        self.assertEqual(mock_post.call_args[0][0], 'https://api.vitepay.com/v1/prod/payments')
        self.assertEqual(json.loads(mock_post.call_args[1]['data']), data)
        self.assertEqual(mock_post.call_args[1]['headers'], {'Content-Type': 'application/json'})

        self.assertEqual(authorization_action['url'], 'https://vitepay.com/some-path-to-pay')

    def test_update_payment(self, get_current_host):
        """
        Play some posts that Vitepay might fire at us.
        """
        order_payment = VitepayOrderPaymentFactory.create(amount=Money(2000, XOF))
        payment = VitepayPaymentFactory.create(order_id='opc-1', order_payment=order_payment)
        authenticity = '69E78BC6C64D43DA76DEB90F911AF213DA9DE89D'
        update_view = reverse('vitepay-status-update')
        data = {
            'success': 1,
            'order_id': payment.order_id,
            'authenticity': authenticity
        }
        response = self.client.post(update_view, data, format='multipart')
        self.assertEqual(response.content, '{"status": "1"}')

    def test_invalid_update_hash(self, get_current_host):
        """
        Test for invalid hash from Vitepay.
        """
        payment = VitepayPaymentFactory.create()
        update_view = reverse('vitepay-status-update')
        data = {
            'success': 1,
            'order_id': payment.order_id,
            'authenticity': 'hashyhashy'
        }
        response = self.client.post(update_view, data, format='multipart')
        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')
        self.assertEqual(data['message'], 'Authenticity incorrect.')

    def test_invalid_order_id(self, get_current_host):
        """
        Test for invalid hash from Vitepay.
        """
        update_view = reverse('vitepay-status-update')
        data = {
            'success': 1,
            'order_id': 999,
            'authenticity': 'hashyhashy'
        }
        response = self.client.post(update_view, data, format='multipart')
        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')
        self.assertEqual(data['message'], 'Order not found.')
