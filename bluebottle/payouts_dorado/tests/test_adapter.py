from requests.exceptions import RequestException, MissingSchema

from datetime import timedelta
from mock import patch, MagicMock
from moneyed.classes import Money
from celery.exceptions import Retry

from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.payouts_dorado import tasks


class TestPayoutBase(BluebottleTestCase):
    """
    Test Payout Adapter
    """

    def setUp(self):
        super(BluebottleTestCase, self).setUp()
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

        self.assertEqual(self.project.status.slug, 'done-complete')
        self.assertEqual(self.project.payout_status, 'needs_approval')


class TestPayoutAdapter(TestPayoutBase):
    @patch('bluebottle.payouts_dorado.tasks.requests.post',
           return_value=type('obj', (object,), {'status_code': 200, 'content': '{"status": "success"}'}))
    def test_payouts_created_trigger_called(self, requests_mock):
        """
        Check trigger to service is been called.
        """

        self.project.payout_status = 'approved'
        self.project.save()

        requests_mock.assert_called_once_with('test', {'project_id': self.project.id, 'tenant': u'test'})
        self.project.refresh_from_db()
        self.assertEqual(self.project.payout_status, 'created')


class TestPayoutExceptions(TestPayoutBase):
    @patch('bluebottle.payouts_dorado.tasks.requests')
    @patch('bluebottle.payouts_dorado.tasks.post_project_data.retry', MagicMock(side_effect=Retry))
    def test_retry_request_failure(self, requests_mock):
        """
        task should retry if request fails
        """
        requests_mock.post.side_effect = RequestException()
        with self.assertRaises(Retry):
            tasks.post_project_data('networkfailure', {})

    @patch('bluebottle.payouts_dorado.tasks.requests')
    @patch('bluebottle.payouts_dorado.tasks.post_project_data.retry', MagicMock(side_effect=Retry))
    def test_not_retry_settings_failure(self, requests_mock):
        """
        task should not retry if settings incorrect
        """
        requests_mock.post.side_effect = MissingSchema()
        with self.assertRaises(ImproperlyConfigured):
            tasks.post_project_data('invalidurl', {})

    @patch('bluebottle.payouts_dorado.tasks.requests.post',
           return_value=type('obj', (object,), {'status_code': 401, 'content': ''}))
    def test_task_failed_request(self, requests_mock):
        """
        Exception raised in post_project_data if request fails
        """
        self.project.payout_status = 'approved'
        with self.assertRaises(SystemError):
            self.project.save()

    @patch('bluebottle.projects.models.logger')
    @override_settings(PAYOUT_SERVICE=None)
    def test_payouts_settings_missing(self, mock_logger):
        """
        Message logged if payout status changed without service settings.
        """

        self.project.payout_status = 'approved'
        self.project.save()

        mock_logger.warning.assert_called_with('Dorado not configured when project payout approved', exc_info=1)
