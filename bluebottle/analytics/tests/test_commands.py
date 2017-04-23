import os
from argparse import ArgumentTypeError
from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase
from mock import patch

from bluebottle.analytics.management.commands.export_engagement_metrics import Command
from bluebottle.test.utils import BluebottleTestCase
from .common import FakeInfluxDBClient

fake_client = FakeInfluxDBClient()


class TestEngagementMetricsUnit(SimpleTestCase):

    def test_validate_date(self):
        with self.assertRaises(ArgumentTypeError):
            Command._validate_date('2017-13-13')
        self.assertEquals('2017-01-01', Command._validate_date('2017-01-01'))

    def test_get_engagement_score(self):
        entry = {'comments': 1,
                 'votes': 1,
                 'donations': 1,
                 'tasks': 1,
                 'fundraisers': 1,
                 'projects': 1}

        self.assertEquals(30, Command.get_engagement_score(entry))

    def test_get_engagement_rating(self):
        self.assertEquals('not engaged', Command.get_engagement_rating(0))
        self.assertEquals('little engaged', Command.get_engagement_rating(1))
        self.assertEquals('little engaged', Command.get_engagement_rating(4))
        self.assertEquals('engaged', Command.get_engagement_rating(5))
        self.assertEquals('engaged', Command.get_engagement_rating(8))
        self.assertEquals('very engaged', Command.get_engagement_rating(9))
        self.assertEquals('invalid engagement score: test', Command.get_engagement_rating('test'))

    @patch('bluebottle.analytics.management.commands.export_engagement_metrics.datetime')
    def test_get_xls_file_name(self, mock_datetime):
        now = datetime(2017, 01, 01)
        mock_datetime.now.return_value = now
        start_date = datetime(2016, 01, 01)
        end_date = datetime(2016, 12, 31)
        self.assertEquals(Command.get_xls_file_name(start_date, end_date),
                          'engagement_report_20160101_20161231_generated_20170101-000000.xlsx')


class TestEngagementMetricsXls(BluebottleTestCase):

    def setUp(self):
        super(TestEngagementMetricsXls, self).setUp()
        self.init_projects()
        self.xls_file_name = 'test.xlsx'
        self.command = Command()

    def test_xls_generation(self):

        with patch.object(self.command, 'get_xls_file_name', return_value=self.xls_file_name):
            call_command(self.command, '--start', '2017-01-01', '--end', '2017-12-31', '--export-to', 'xls')
            self.assertTrue(os.path.isfile(os.path.join(settings.PROJECT_ROOT, self.xls_file_name)), True)

    def tearDown(self):
        os.remove(os.path.join(settings.PROJECT_ROOT, self.xls_file_name))
