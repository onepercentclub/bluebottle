from unittest.mock import patch

from bluebottle.funding.exception import PaymentException
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentFactory, LipishaPaymentProviderFactory
from bluebottle.funding_lipisha.utils import check_payment_status
from bluebottle.test.utils import BluebottleTestCase


lipisha_success_response = {
    'content': [
        {
            'transaction': 'A35EE9256',
            'transaction_account_name': 'Donations',
            'transaction_account_number': '03858',
            'transaction_amount': '2500.0000',
            'transaction_currency': 'KES',
            'transaction_date': '2017-05-19 00:15:02',
            'transaction_email': '',
            'transaction_method': 'Paybill (M-Pesa)',
            'transaction_mobile_number': '31715283569',
            'transaction_name': 'ROSE ONESMUS RACHEL',
            'transaction_reference': '4312',
            'transaction_reversal_status': 'None',
            'transaction_reversal_status_id': '1',
            'transaction_status': 'Completed',
            'transaction_type': 'Payment'
        }
    ],
    'status': {
        'status': 'SUCCESS',
        'status_code': 0,
        'status_description': 'Transactions Found'
    }
}


lipisha_failed_response = {
    'content': [
        {
            'transaction': 'A35EE9256',
            'transaction_account_name': 'Donations',
            'transaction_account_number': '03858',
            'transaction_amount': '2500.0000',
            'transaction_currency': 'KES',
            'transaction_date': '2017-05-19 00:15:02',
            'transaction_email': '',
            'transaction_method': 'Paybill (M-Pesa)',
            'transaction_mobile_number': '31715283569',
            'transaction_name': 'ROSE ONESMUS RACHEL',
            'transaction_reference': '4312',
            'transaction_reversal_status': 'None',
            'transaction_reversal_status_id': '1',
            'transaction_status': 'Cancelled',
            'transaction_type': 'Payment'
        }
    ],
    'status': {
        'status': 'SUCCESS',
        'status_code': 0,
        'status_description': 'Transactions Found'
    }
}


lipisha_not_found_response = {
    'content': [],
    'status': {
        'status': 'SUCCESS',
        'status_code': 4000,
        'status_description': 'Transactions Not Found'
    }
}


lipisha_double_success_response = {
    'content': [
        {
            'transaction': 'A35EE9256',
            'transaction_account_name': 'Donations',
            'transaction_account_number': '03858',
            'transaction_amount': '2500.0000',
            'transaction_currency': 'KES',
            'transaction_date': '2017-05-19 00:15:02',
            'transaction_email': '',
            'transaction_method': 'Paybill (M-Pesa)',
            'transaction_mobile_number': '31715283569',
            'transaction_name': 'ROSE ONESMUS RACHEL',
            'transaction_reference': '4312',
            'transaction_reversal_status': 'None',
            'transaction_reversal_status_id': '1',
            'transaction_status': 'Completed',
            'transaction_type': 'Payment'
        },
        {
            'transaction': 'A35EE92235',
            'transaction_account_name': 'Donations',
            'transaction_account_number': '03858',
            'transaction_amount': '3500.0000',
            'transaction_currency': 'KES',
            'transaction_date': '2017-05-19 00:33:02',
            'transaction_email': '',
            'transaction_method': 'Paybill (M-Pesa)',
            'transaction_mobile_number': '317112355',
            'transaction_name': 'HENK ONESMUS RACHEL',
            'transaction_reference': '4312',
            'transaction_reversal_status': 'None',
            'transaction_reversal_status_id': '1',
            'transaction_status': 'Completed',
            'transaction_type': 'Payment'
        }

    ],
    'status': {
        'status': 'SUCCESS',
        'status_code': 0,
        'status_description': 'Transactions Found'
    }
}


class LipishaPaymentUpdateTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        LipishaPaymentProvider.objects.all().delete()
        self.provider = LipishaPaymentProviderFactory.create()

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_success_response)
    def test_success(self, mock_client):
        payment = LipishaPaymentFactory.create()
        check_payment_status(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'succeeded')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_failed_response)
    def test_failed(self, mock_client):
        payment = LipishaPaymentFactory.create()
        check_payment_status(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_not_found_response)
    def test_not_found(self, mock_client):
        payment = LipishaPaymentFactory.create()
        with self.assertRaisesMessage(
                PaymentException,
                "Payment could not be verified yet. Payment not found."
        ):
            check_payment_status(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_double_success_response)
    def test_found_two(self, mock_client):
        payment = LipishaPaymentFactory.create()
        with self.assertRaisesMessage(
                PaymentException,
                f"Found multiple payments with code {payment.unique_id}."
        ):
            check_payment_status(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'new')
