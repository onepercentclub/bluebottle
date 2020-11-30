from django.contrib.messages import get_messages
from django.urls import reverse
from djmoney.money import Money
from mock import patch

from bluebottle.funding.tests.factories import (
    DonorFactory, FundingFactory
)
from bluebottle.funding_flutterwave.tests.factories import FlutterwaveBankAccountFactory
from bluebottle.test.utils import BluebottleAdminTestCase

success_response = {
    'status': 'success',
    'data': {
        'status': 'successful',
        'amount': 1000,
        'currency': 'NGN'
    }
}


class FlutterwavePaymentAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FlutterwavePaymentAdminTestCase, self).setUp()
        bank_account = FlutterwaveBankAccountFactory.create()
        funding = FundingFactory.create(bank_account=bank_account)
        self.client.force_login(self.superuser)
        self.donation = DonorFactory(
            amount=Money(10000, 'NGN'),
            activity=funding
        )

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=success_response)
    def test_sync_payment(self, flutterwave_post):
        sync_url = reverse('admin:funding_donation_sync', args=(self.donation.id,))
        response = self.client.get(sync_url)
        messages = list(get_messages(response.wsgi_request))
        self.donation.refresh_from_db()
        self.assertEqual(
            messages[0].message,
            'Generated missing payment')
        self.assertEqual(
            messages[1].message,
            'Checked payment status for {}'.format((self.donation.payment)))
        self.assertEqual(self.donation.status, 'succeeded')
