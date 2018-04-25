from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch

from bluebottle.payments_beyonic.tests.factory_models import BeyonicPaymentFactory
from bluebottle.test.utils import BluebottleTestCase


beyonic_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'beyonic',
            'currency': 'UGX',
            'merchant_id': '123456',
            'merchant_key': '123456789',
            'live': True
        }
    ]
}


@override_settings(**beyonic_settings)
class BeyonicPaymentUpdateTest(BluebottleTestCase):
    def setUp(self):
        super(BeyonicPaymentUpdateTest, self).setUp()
        self.payment = BeyonicPaymentFactory.create(transaction_reference='123')

    @patch('beyonic.CollectionRequest.get', return_value={'status': 'successful'})
    def test_valid_update(self, mock_get):
        data = {
            'data': {
                'status': 'successful',
                'transaction': {'id': 17},
                'collection_request': {'id': '123'}
            }
        }
        response = self.client.post(reverse('beyonic-payment-update'), data, format='json')
        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, 'settled')

    @patch('beyonic.CollectionRequest.get', return_value={'status': 'failed'})
    def test_failed_update(self, mock_get):
        data = {
            'data': {
                'status': 'successful',
                'transaction': {'id': 17},
                'collection_request': {'id': '123'}
            }
        }
        response = self.client.post(reverse('beyonic-payment-update'), data, format='json')
        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, 'failed')

    @patch('beyonic.CollectionRequest.get', return_value={'status': 'successful'})
    def test_invalid_update(self, mock_get):
        data = {
            'data': {
                'status': 'successful',
                'transaction': {'id': 17},
                'collection_request': {'id': '456'}
            }
        }
        response = self.client.post(reverse('beyonic-payment-update'), data, format='json')
        self.assertEqual(response.status_code, 404)
