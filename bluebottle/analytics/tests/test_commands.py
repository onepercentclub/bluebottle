from django.test import SimpleTestCase
from bluebottle.analytics.management.commands.export_engagement_metrics import Command
from argparse import ArgumentTypeError


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
