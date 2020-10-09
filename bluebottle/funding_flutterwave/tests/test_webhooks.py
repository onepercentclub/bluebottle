from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from rest_framework.status import HTTP_200_OK

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentFactory, FlutterwavePaymentProviderFactory
from bluebottle.test.utils import BluebottleTestCase

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'pub_key': '123456789123456789',
            'sec_key': '123456789123456789',
        },
    ]
}


@override_settings(**flutterwave_settings)
class FlutterwaveWebhookTest(BluebottleTestCase):

    def setUp(self):
        super(FlutterwaveWebhookTest, self).setUp()
        FlutterwavePaymentProviderFactory.create()
        self.webhook_url = reverse('flutterwave-payment-webhook')

    def test_webhook(self):
        donation = DonationFactory.create()
        payment = FlutterwavePaymentFactory.create(
            donation=donation,
            tx_ref=donation.id
        )
        payload = {
            "event": "charge.completed",
            "data": {
                "id": 313646423,
                "tx_ref": donation.id,
                "flw_ref": "2Scale/FLW336518359",
                "device_fingerprint": "8a3ceecb7ac72d8b0e7e0e7b5627f966",
                "amount": 50000,
                "currency": "NGN",
                "charged_amount": 50700,
                "app_fee": 700,
                "merchant_fee": 0,
                "processor_response": "Approved by Financial Institution",
                "auth_model": "PIN",
                "ip": "160.152.228.40",
                "narration": "CARD Transaction ",
                "status": "successful",
                "payment_type": "card",
                "created_at": "2020-09-29T14:27:45.000Z",
                "account_id": 179031,
                "customer": {
                    "id": 225543006,
                    "name": "Anonymous customer",
                    "phone_number": "unknown",
                    "email": "henk@gmail.com",
                    "created_at": "2020-09-29T14:24:30.000Z"
                },
                "card": {
                    "first_6digits": "123456",
                    "last_4digits": "7890",
                    "issuer": "MASTERCARD ZENITH BANK DEBIT STANDARD",
                    "country": "NG",
                    "type": "MASTERCARD",
                    "expiry": "08/23"
                }
            }
        }
        with patch('bluebottle.funding_flutterwave.utils.post', return_value=payload):
            response = self.client.post(self.webhook_url, data=payload)
        self.assertEqual(response.status_code, HTTP_200_OK)
        payment.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(payment.status, 'succeeded')
        self.assertEqual(donation.status, 'succeeded')

    def test_webhook_without_payment(self):
        donation = DonationFactory.create()
        payload = {
            "data": {
                "id": 1231,
                "tx_ref": donation.id,
                "flw_ref": "FLW-MOCK-3aa21c8ed962e5b64a986403fc60fa2d",
                "amount": 17500,
                "currency": "NGN",
                "status": "successful",
                "customer": {
                    "id": 154159,
                },
            },
            "event": "charge.completed"
        }
        with patch('bluebottle.funding_flutterwave.utils.post', return_value=payload):
            response = self.client.post(self.webhook_url, data=payload)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(donation.payment.status, 'succeeded')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'succeeded')

    def test_webhook_bank_transfer_without_payment(self):
        donation = DonationFactory.create()
        payload = {
            "data": {
                "id": 1231,
                "tx_ref": donation.id,
                "flw_ref": "FLW-MOCK-2345235235",
                "amount": 19500,
                "currency": "NGN",
                "status": "successful",
                "amountsettledforthistransaction": 17500,
                "customer": {
                    "id": 154159,
                },
            },
            "event": "charge.completed"
        }
        with patch('bluebottle.funding_flutterwave.utils.post', return_value=payload):
            response = self.client.post(self.webhook_url, data=payload)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(donation.payment.status, 'succeeded')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'succeeded')
        self.assertEqual(donation.amount.amount, 17500)
        self.assertEqual(donation.payout_amount.amount, 17500)

    def test_webhook_without_payment_another(self):
        donation = DonationFactory.create()
        payload = {
            "event": "charge.completed",
            "data": {
                "id": 313646423,
                "tx_ref": donation.id,
                "flw_ref": "2Scale/234235",
                "device_fingerprint": "234523455",
                "amount": 50000,
                "currency": "NGN",
                "charged_amount": 50700,
                "app_fee": 700,
                "merchant_fee": 0,
                "processor_response": "Approved by Financial Institution",
                "auth_model": "PIN",
                "ip": "160.152.228.40",
                "narration": "CARD Transaction ",
                "status": "successful",
                "payment_type": "card",
                "created_at": "2020-09-29T14:27:45.000Z",
                "account_id": 179031,
                "customer": {
                    "id": 225543006,
                    "name": "Anonymous customer",
                    "phone_number": "unknown",
                    "email": "henkie@gmail.com",
                    "created_at": "2020-09-29T14:24:30.000Z"
                },
                "card": {
                    "first_6digits": "234234",
                    "last_4digits": "2343",
                    "issuer": "MASTERCARD ZENITH BANK DEBIT STANDARD",
                    "country": "NG",
                    "type": "MASTERCARD",
                    "expiry": "08/23"
                }
            }
        }
        with patch('bluebottle.funding_flutterwave.utils.post', return_value=payload):
            response = self.client.post(self.webhook_url, data=payload)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(donation.payment.status, 'succeeded')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'succeeded')
