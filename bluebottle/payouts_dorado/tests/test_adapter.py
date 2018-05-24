from datetime import timedelta
from mock import patch
from moneyed.classes import Money
import requests

from django.utils.timezone import now
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.payouts_dorado.adapters import DoradoPayoutAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class TestPayoutAdapter(BluebottleTestCase):
    """
    Test Payout Adapter
    """

    def setUp(self):
        super(TestPayoutAdapter, self).setUp()
        self.init_projects()
        campaign = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=campaign,
                                             amount_asked=Money(500, 'EUR'))

        order = OrderFactory()
        DonationFactory.create_batch(7, project=self.project,
                                     amount=Money(100, 'EUR'), order=order)
        order.locked()
        order.success()
        order.save()

        order = OrderFactory()
        DonationFactory.create_batch(4, project=self.project,
                                     amount=Money(150, 'USD'), order=order)
        order.locked()
        order.success()
        order.save()

        yesterday = now() - timedelta(days=1)
        self.project.deadline = yesterday
        self.project.save()

        self.mock_response = requests.Response()
        self.mock_response.status_code = 200

        self.adapter = DoradoPayoutAdapter(self.project)

    @override_settings(PAYOUT_SERVICE={'url': 'http://test.nu'})
    def test_payouts_created_trigger_called(self):
        """
        Check trigger to service is been called.
        """

        self.assertEqual(self.project.status.slug, 'done-complete')
        self.assertEqual(self.project.payout_status, 'needs_approval')

        with patch('requests.post', return_value=self.mock_response) as request_mock:
            self.adapter.trigger_payout()

        request_mock.assert_called_once_with('test', {'project_id': self.project.id, 'tenant': u'test'})

    @patch('bluebottle.projects.models.logger')
    @override_settings(PAYOUT_SERVICE=None)
    def test_payouts_settings_missing(self, mock_logger):
        """
        Message logged if payout status changed without service settings.
        """
        self.assertEqual(self.project.status.slug, 'done-complete')
        self.assertEqual(self.project.payout_status, 'needs_approval')

        with self.assertRaises(ImproperlyConfigured):
            self.adapter.trigger_payout()
