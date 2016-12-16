from mock import patch

from django.utils import timezone
from django.test.utils import override_settings
from django.test import SimpleTestCase

from bluebottle.analytics import signals
from bluebottle.analytics.tasks import queue_analytics_record
from bluebottle.analytics.backends import InfluxExporter

from .common import FakeInfluxDBClient, FakeModel, FakeModelTwo

fake_client = FakeInfluxDBClient()


def do_nothing(**kwargs):
    pass


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(InfluxExporter, 'process')
@patch.object(InfluxExporter, 'client', fake_client)
class TestAnalyticsQueue(SimpleTestCase):
    def test_tags_generation(self, mock_process):
        tags = {
            'tenant': 'test',
            'type': 'order'
        }
        fields = {
            'amount': 100
        }

        now = timezone.now()
        queue_analytics_record(timestamp=now, tags=tags, fields=fields)
        mock_process.assert_called_with(now, tags, fields)


@override_settings(ANALYTICS_ENABLED=True,
                   CELERY_RESULT_BACKEND='amqp')
class TestAnalyticsSignalWithCelery(SimpleTestCase):
    @patch.object(signals.connection, 'schema_name', 'test')
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
    @patch.object(signals.connection, 'schema_name', 'test')
    def test_metric_type(self):
        tags = {
            'tenant': 'test',
            'type': 'fake_model_two'
        }

        with patch('bluebottle.analytics.signals.queue_analytics_record') as mock_queue:
            mock_queue.side_effect = do_nothing
            signals.post_save_analytics(None, FakeModelTwo(), **{'created': True})

            args, kwargs = mock_queue.call_args
            self.assertEqual(kwargs['tags'], tags)
