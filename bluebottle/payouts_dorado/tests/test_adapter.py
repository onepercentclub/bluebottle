from datetime import timedelta

import requests
from django.test.utils import override_settings
from django.utils.timezone import now
# from mock import patch
from moneyed.classes import Money

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter
from bluebottle.test.utils import BluebottleTestCase


class TestPayoutAdapter(BluebottleTestCase):
    """
    Test Payout Adapter
    """

    def setUp(self):
        super(TestPayoutAdapter, self).setUp()
        self.funding = FundingFactory.create(target=Money(500, 'EUR'), status='open')
        DonationFactory.create_batch(
            7,
            activity=self.funding,
            status='succeeded',
            amount=Money(100, 'EUR'))

        yesterday = now() - timedelta(days=1)
        self.funding.deadline = yesterday
        self.funding.save()

        self.mock_response = requests.Response()
        self.mock_response.status_code = 200

        self.adapter = DoradoPayoutAdapter(self.funding)

    @override_settings(PAYOUT_SERVICE={'url': 'http://example.com'})
    def test_payouts_created_trigger_called(self):
        """
        Check trigger to service is been called.
        """
        pass
        # with patch('requests.post', return_value=self.mock_response) as request_mock:
        #    self.funding.transitions.succeed()

        # FIXME !
        # Test that the adapater will trigger a call to Payout app when Funding is succeeded.
        # request_mock.assert_called_once_with('test', {'project_id': self.funding.id, 'tenant': u'test'})
