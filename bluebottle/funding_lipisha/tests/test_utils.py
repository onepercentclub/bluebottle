from mock import patch

from bluebottle.funding.exception import PaymentException
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentFactory, LipishaPaymentProviderFactory
from bluebottle.funding_lipisha.utils import check_payment_status
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


class LipishaPaymentUpdateTestCase(BluebottleTestCase):

    def setUp(self):
        super(LipishaPaymentUpdateTestCase, self).setUp()
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
        check_payment_status(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')

    @patch('lipisha.Lipisha._make_api_call', return_value=lipisha_double_success_response)
    def test_found_two(self, mock_client):
        payment = LipishaPaymentFactory.create()
        with self.assertRaisesMessage(
                PaymentException,
                "Found multiple payments with code {}.".format(payment.unique_id)
        ):
            check_payment_status(payment)
