import json
import os
from datetime import datetime

from django.conf import settings
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch

from bluebottle.analytics import signals, utils
from bluebottle.analytics.backends import FileExporter
from bluebottle.analytics.tasks import queue_analytics_record
from .common import FakeModel, FakeModelTwo


def do_nothing(**kwargs):
    pass


@override_settings(ANALYTICS_ENABLED=True)
@override_settings(ANALYTICS_BACKENDS={
    'file': {
        'handler_class': 'bluebottle.analytics.backends.FileExporter',
        'base_dir': os.path.join(settings.PROJECT_ROOT, 'logs', 'analytics'),
        'measurement': 'saas',
    }
})
class TestFileAnalyticsQueue(SimpleTestCase):
    def setUp(self):
        super(TestFileAnalyticsQueue, self).setUp()

        self.tags = {
            'tenant': 'test',
            'type': 'order'
        }

        self.fields = {
            'amount': 100
        }

        base_dir = os.path.join(settings.PROJECT_ROOT, 'logs', 'analytics')
        self.log_dir = os.path.join(base_dir, self.tags['tenant'])

    @patch.object(FileExporter, 'process')
    def test_file_exporter(self, mock_process):
        timestamp = timezone.now()
        queue_analytics_record(timestamp=timestamp, tags=self.tags, fields=self.fields)
        mock_process.assert_called_with(timestamp, self.tags, self.fields)

    def test_log_file_generated(self):
        timestamp = datetime(2016, 12, 31, 23, 59, 59, 123456)
        queue_analytics_record(timestamp=timestamp, tags=self.tags, fields=self.fields)

        log_path = os.path.join(self.log_dir, '{}.log'.format(timestamp.strftime('%Y-%m-%d')))
        self.assertTrue(os.path.exists(log_path))

        # Get last line from log
        with open(log_path) as infile:
            for line in infile:
                if not line.strip('\n'):
                    continue
                last_line = line

        json_logs = json.loads(last_line)
        log = json_logs[0]
        self.assertEqual(len(json_logs), 1)
        self.assertEqual(log['fields'], self.fields)
        self.assertEqual(log['tags'], self.tags)
        self.assertEqual(log['time'], 1483228799123456)
        self.assertEqual(log['measurement'], 'saas')


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
