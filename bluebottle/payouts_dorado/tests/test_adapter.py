from datetime import timedelta
from django.utils.timezone import now
from mock import patch
from moneyed.classes import Money

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


@patch('bluebottle.payouts_dorado.adapters.requests.post',
       return_value=type('obj', (object,), {'status_code': 200, 'content': '{"status": "success"}'}))
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

    def test_payouts_created_trigger_called(self, requests_mock):
        """
        Check trigger to service is been called.
        """
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

        self.assertEqual(self.project.status.slug, 'done-complete')
        self.assertEqual(self.project.payout_status, 'needs_approval')

        self.project.payout_status = 'approved'
        self.project.save()

        requests_mock.assert_called_once_with('test', {'project_id': self.project.id, 'tenant': u'test'})
        self.assertEqual(self.project.payout_status, 'created')
