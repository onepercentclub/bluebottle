import json

from django.urls import reverse
from mock import patch
from rest_framework.status import HTTP_200_OK

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentFactory, LipishaPaymentProviderFactory, \
    LipishaBankAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase

lipisha_success_response = {
    u'content': [
        {
            u'transaction': u'A35EE9256',
            u'transaction_account_name': u'Donations',
            u'transaction_account_number': u'03858',
            u'transaction_amount': u'2500.0000',
            u'transaction_currency': u'KES',
            u'transaction_date': u'2017-05-19 00:15:02',
            u'transaction_email': u'',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction_mobile_number': u'31715283569',
            u'transaction_name': u'ROSE ONESMUS RACHEL',
            u'transaction_reference': u'4312',
            u'transaction_reversal_status': u'None',
            u'transaction_reversal_status_id': u'1',
            u'transaction_status': u'Completed',
            u'transaction_type': u'Payment'
        }
    ],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 0,
        u'status_description': u'Transactions Found'
    }
}

lipisha_failed_response = {
    u'content': [
        {
            u'transaction': u'A35EE9256',
            u'transaction_account_name': u'Donations',
            u'transaction_account_number': u'03858',
            u'transaction_amount': u'2500.0000',
            u'transaction_currency': u'KES',
            u'transaction_date': u'2017-05-19 00:15:02',
            u'transaction_email': u'',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction_mobile_number': u'31715283569',
            u'transaction_name': u'ROSE ONESMUS RACHEL',
            u'transaction_reference': u'4312',
            u'transaction_reversal_status': u'None',
            u'transaction_reversal_status_id': u'1',
            u'transaction_status': u'Cancelled',
            u'transaction_type': u'Payment'
        }
    ],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 0,
        u'status_description': u'Transactions Found'
    }
}

lipisha_not_found_response = {
    u'content': [],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 4000,
        u'status_description': u'Transactions Not Found'
    }
}

lipisha_double_success_response = {
    u'content': [
        {
            u'transaction': u'A35EE9256',
            u'transaction_account_name': u'Donations',
            u'transaction_account_number': u'03858',
            u'transaction_amount': u'2500.0000',
            u'transaction_currency': u'KES',
            u'transaction_date': u'2017-05-19 00:15:02',
            u'transaction_email': u'',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction_mobile_number': u'31715283569',
            u'transaction_name': u'ROSE ONESMUS RACHEL',
            u'transaction_reference': u'4312',
            u'transaction_reversal_status': u'None',
            u'transaction_reversal_status_id': u'1',
            u'transaction_status': u'Completed',
            u'transaction_type': u'Payment'
        },
        {
            u'transaction': u'A35EE92235',
            u'transaction_account_name': u'Donations',
            u'transaction_account_number': u'03858',
            u'transaction_amount': u'3500.0000',
            u'transaction_currency': u'KES',
            u'transaction_date': u'2017-05-19 00:33:02',
            u'transaction_email': u'',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction_mobile_number': u'317112355',
            u'transaction_name': u'HENK ONESMUS RACHEL',
            u'transaction_reference': u'4312',
            u'transaction_reversal_status': u'None',
            u'transaction_reversal_status_id': u'1',
            u'transaction_status': u'Completed',
            u'transaction_type': u'Payment'
        }

    ],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 0,
        u'status_description': u'Transactions Found'
    }
}


class LipishaPaymentInitiateTestCase(BluebottleTestCase):

    def setUp(self):
        super(LipishaPaymentInitiateTestCase, self).setUp()
        LipishaPaymentProvider.objects.all().delete()
        self.provider = LipishaPaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.account = LipishaBankAccountFactory.create()
        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.account)
        self.donation = DonorFactory.create(activity=self.funding)
        self.webhook = reverse('lipisha-payment-webhook')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_success_response)
    def test_initiate(self, mock_client):
        data = {
            'api_key': self.provider.api_key,
            'api_signature': self.provider.api_signature,
            'api_version': '2.0.0',
            'api_type': 'Initiate',
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': '',
            'transaction': '7ACCB5CC8',
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'SUCCESS')
        payment = LipishaPayment.objects.get()
        self.assertEqual(payment.status, 'succeeded')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_failed_response)
    def test_initiate_failed(self, mock_client):
        data = {
            'api_key': self.provider.api_key,
            'api_signature': self.provider.api_signature,
            'api_version': '2.0.0',
            'api_type': 'Initiate',
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': '',
            'transaction': '7ACCB5CC8',
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Failed',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'SUCCESS')
        payment = LipishaPayment.objects.get()
        self.assertEqual(payment.status, 'failed')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_success_response)
    def test_acknowledge_wrong_key(self, mock):
        data = {
            'api_key': 'hacker-key',
            'api_signature': self.provider.api_signature,
            'api_version': '2.0.0',
            'api_type': 'Initiate',
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': '',
            'transaction': '7ACCB5CC8',
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'FAIL')


class LipishaPaymentAcknowledgeTestCase(BluebottleTestCase):

    def setUp(self):
        super(LipishaPaymentAcknowledgeTestCase, self).setUp()
        LipishaPaymentProvider.objects.all().delete()
        self.provider = LipishaPaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.account = LipishaBankAccountFactory.create()
        self.funding = FundingFactory.create(initiative=self.initiative, bank_account=self.account)
        self.donation = DonorFactory.create(activity=self.funding)
        self.webhook = reverse('lipisha-payment-webhook')
        self.payment = LipishaPaymentFactory.create(
            donation=self.donation,
            unique_id='some-id',
            transaction='7ACCB5CC8'
        )

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_success_response)
    def test_acknowledge(self, mock_client):
        data = {
            'api_key': self.provider.api_key,
            'api_signature': self.provider.api_signature,
            'api_version': '2.0.0',
            'api_type': 'Acknowledge',
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': self.payment.unique_id,
            'transaction': '7ACCB5CC8',
            'transaction_reference': self.payment.transaction,
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'SUCCESS')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'succeeded')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_failed_response)
    def test_acknowledge_failed(self, mock_client):
        data = {
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': self.payment.unique_id,
            'transaction': self.payment.transaction,
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Failed',
            'transaction_mobile': '25471000000',
            'api_key': self.provider.api_key,
            'api_type': 'Acknowledge',
            'api_signature': self.provider.api_signature,
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'SUCCESS')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_success_response)
    def test_acknowledge_wrong_key(self, mock_client):
        data = {
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': self.payment.unique_id,
            'transaction': self.payment.transaction,
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Failed',
            'transaction_mobile': '25471000000',
            'api_key': '98762323454',
            'api_type': 'Acknowledge',
            'api_signature': self.provider.api_signature,
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'FAIL')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'new')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_not_found_response)
    def test_acknowledge_not_found(self, mock_client):
        data = {
            'transaction_account': self.account.mpesa_code,
            'transaction_account_number': self.account.mpesa_code,
            'transaction_merchant_reference': self.payment.unique_id,
            'transaction': self.payment.transaction,
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Failed',
            'transaction_mobile': '25471000000',
            'api_key': self.provider.api_key,
            'api_type': 'Acknowledge',
            'api_signature': self.provider.api_signature,
        }
        response = self.client.post(self.webhook, data, format='multipart')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(json.loads(response.content)['transaction_status'], 'SUCCESS')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
