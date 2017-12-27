from bluebottle.payments_docdata.gateway import DocdataClient, Amount, Shopper, Name, Destination, Address, Merchant

from bunch import bunchify
from mock import patch, Mock

from bluebottle.test.utils import BluebottleTestCase


class DocdataClientMock():
    class service():
        @staticmethod
        def create(*args, **kwargs):
            return bunchify({
                'createSuccess': {
                    'key': 'HAZZAHAZZA'
                }
            })

    class factory:
        @staticmethod
        def create(ns):
            return Mock()


@patch('bluebottle.payments_docdata.gateway.Client', return_value=DocdataClientMock())
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
