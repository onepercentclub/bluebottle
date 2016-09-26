from mock import patch

from django.utils import timezone
from django.test.utils import override_settings
from django.test import SimpleTestCase

from bluebottle.test.factory_models.wallposts import TextWallpostFactory

from bluebottle.analytics import signals
from bluebottle.analytics.utils import queue_analytics_record
from bluebottle.analytics.backends import InfluxExporter

from .common import FakeInfluxDBClient, FakeModel


fake_client = FakeInfluxDBClient()


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(InfluxExporter, 'process')
@patch.object(InfluxExporter, 'client', fake_client)
class TestRecordAnalytics(SimpleTestCase):
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
@patch.object(queue_analytics_record, 'delay')
class TestAnalyticsCelery(SimpleTestCase):
    @patch.object(signals.connection, 'schema_name', 'test')
    def test_tags_generation(self, mock_delay):
        tags = {
            'tenant': 'test',
            'type': 'fake'
        }
        fields = {}

        signals.post_save_analytics(None, FakeModel(), **{'created': True})

        args, kwargs = mock_delay.call_args
        self.assertEqual(kwargs['tags'], tags)
        self.assertEqual(kwargs['fields'], fields)
