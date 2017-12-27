from bluebottle.payments.exception import PaymentException
from bluebottle.payments_docdata.gateway import (
    DocdataClient, Amount, Shopper, Name, Destination, Address, Merchant
)
from bluebottle.payments_docdata.tests.factory_models import DocdataDirectdebitPaymentFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory

from bunch import bunchify
from mock import patch, Mock

from bluebottle.test.utils import BluebottleTestCase


class DocdataClientSuccessMock():
    class service():
        @staticmethod
        def create(*args, **kwargs):
            return bunchify({
                'createSuccess': {
                    'key': 'HAZZAHAZZA'
                }
            })

        @staticmethod
        def start(*args, **kwargs):
            return bunchify({
                'startSuccess': {
                    'paymentId': 'GHGHGHG'
                }
            })

    class factory:
        @staticmethod
        def create(ns):
            return Mock()


@patch('bluebottle.payments_docdata.gateway.Client', return_value=DocdataClientSuccessMock())
class DocdataGatewayTestCase(BluebottleTestCase):

    def test_create(self, mock_client):
        credentials = {
            'merchant_name': 'test',
            'merchant_password': 'top-secret',
        }
        self.gateway = DocdataClient(credentials)

        merchant = Merchant('test', 'top-secret')

        amount = Amount(35, 'EUR')
        name1 = Name('Henk', 'Wijngaarden')
        shopper = Shopper(12, name1, 'henk@truck.nl', 'en')

        name2 = Name('Plat', 'Form')
        address = Address('s Gravenhekje', '1', 'A', '1011TG', 'Amsterdam', 'NH', 'NL')

        bill_to = Destination(name2, address)

        result = self.gateway.create(
            merchant=merchant,
            payment_id='123',
            total_gross_amount=amount,
            shopper=shopper,
            bill_to=bill_to,
            description='Donation',
            receiptText='Thanks'
        )

        self.assertEqual(result, {'order_id': '123-1', 'order_key': 'HAZZAHAZZA'})

    def test_start_remote_payment(self, mock_client):
        credentials = {
            'merchant_name': 'test',
            'merchant_password': 'top-secret',
        }
        self.gateway = DocdataClient(credentials)
        order_payment = OrderPaymentFactory()
        payment = DocdataDirectdebitPaymentFactory(
            order_payment=order_payment
        )

        result = self.gateway.start_remote_payment(order_key='123', payment=payment)
        self.assertEqual(result, 'GHGHGHG')


class DocdataClientErrorMock():
    class service():
        @staticmethod
        def create(*args, **kwargs):
            return bunchify({
                'createError': {
                    'error': {
                        '_code': '007',
                        'value': 'It all went kaboom'
                    }
                }
            })

        @staticmethod
        def start(*args, **kwargs):
            return bunchify({
                'createError': {
                    'error': {
                        '_code': '044',
                        'value': 'OMG'
                    }
                }
            })

    class factory:
        @staticmethod
        def create(ns):
            return Mock()


@patch('bluebottle.payments_docdata.gateway.Client', return_value=DocdataClientErrorMock())
class DocdataGatewayErrorTestCase(BluebottleTestCase):

    def test_create(self, mock_client):
        credentials = {
            'merchant_name': 'test',
            'merchant_password': 'top-secret',
        }
        self.gateway = DocdataClient(credentials)

        merchant = Merchant('test', 'top-secret')

        amount = Amount(35, 'EUR')
        name1 = Name('Henk', 'Wijngaarden')
        shopper = Shopper(12, name1, 'henk@truck.nl', 'en')

        name2 = Name('Plat', 'Form')
        address = Address('s Gravenhekje', '1', 'A', '1011TG', 'Amsterdam', 'NH', 'NL')

        bill_to = Destination(name2, address)

        with self.assertRaisesMessage(PaymentException, 'It all went kaboom'):
            self.gateway.create(
                merchant=merchant,
                payment_id='123',
                total_gross_amount=amount,
                shopper=shopper,
                bill_to=bill_to,
                description='Donation',
                receiptText='Thanks'
            )

    def test_start_remote_payment(self, mock_client):
        credentials = {
            'merchant_name': 'test',
            'merchant_password': 'top-secret',
        }
        self.gateway = DocdataClient(credentials)
        order_payment = OrderPaymentFactory()
        payment = DocdataDirectdebitPaymentFactory(
            order_payment=order_payment
        )

        with self.assertRaisesMessage(PaymentException, 'OMG'):
            self.gateway.start_remote_payment(order_key='123', payment=payment)
