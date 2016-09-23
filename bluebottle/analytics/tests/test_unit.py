from mock import patch

from django.utils import timezone
from django.test.utils import override_settings
from django.test import SimpleTestCase

from bluebottle.analytics.utils import queue_analytics_record
from bluebottle.analytics.backends import InfluxExporter


class FakeInfluxDBClient():
    def __init__(self, *args):
        pass

    def write_points(self, **kwargs):
        pass


@override_settings(ANALYTICS_ENABLED=True)
@patch.object(InfluxExporter, '_client')
@patch.object(InfluxExporter, 'process')
class TestProjectAnalytics(SimpleTestCase):
    def test_tags_generation(self, mock_process, mock_client):
        tags = {
            'tenant': 'test',
            'type': 'order'
        }
        fields = {
            'amount': 100
        }

        
        mock_client.return_value = FakeInfluxDBClient()
        now = timezone.now()
        queue_analytics_record(timestamp=now, tags=tags, fields=fields)
        mock_process.assert_called_with(now, tags, fields)
