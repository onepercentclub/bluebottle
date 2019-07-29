from django.test import SimpleTestCase
from django.test.utils import override_settings
from mock import patch

from bluebottle.analytics import signals, utils
from .common import FakeModel, FakeModelTwo


def do_nothing(**kwargs):
    pass


@override_settings(ANALYTICS_ENABLED=True, CELERY_RESULT_BACKEND='amqp')
class TestAnalyticsSignalWithCelery(SimpleTestCase):
    @patch.object(utils.connection, 'schema_name', 'test')
    def test_delay_called(self):
        tags = {
            'tenant': 'test',
            'type': 'fake'
        }
        fields = {}

        with patch('bluebottle.analytics.tasks.queue_analytics_record.delay') as mock_delay:
            signals.post_save_analytics(None, FakeModel(), **{'created': True})

            args, kwargs = mock_delay.call_args
            self.assertEqual(kwargs['tags'], tags)
            self.assertEqual(kwargs['fields'], fields)


@override_settings(ANALYTICS_ENABLED=True)
class TestAnalyticsPostSave(SimpleTestCase):
    @patch.object(utils.connection, 'schema_name', 'test')
    def test_metric_type(self):
        tags = {
            'tenant': 'test',
            'type': 'fake_model_two'
        }

        with patch('bluebottle.analytics.utils.queue_analytics_record') as mock_queue:
            mock_queue.side_effect = do_nothing
            signals.post_save_analytics(None, FakeModelTwo(), **{'created': True})

            args, kwargs = mock_queue.call_args
            self.assertEqual(kwargs['tags'], tags)
