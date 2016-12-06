from django.core.urlresolvers import reverse

from rest_framework import status
from fluent_contents.models import Placeholder

from bluebottle.cms.models import StatsContent, QuotesContent, ResultsContent

from bluebottle.test.factory_models.surveys import SurveyFactory
from bluebottle.test.factory_models.cms import (
    ResultPageFactory, StatFactory, StatsFactory,
    QuotesFactory, QuoteFactory
)
from bluebottle.test.utils import BluebottleTestCase


class ResultPageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(ResultPageTestCase, self).setUp()

        self.page = ResultPageFactory()
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('result-page-detail', kwargs={'pk': self.page.id})

    def test_results_stats(self):
        self.stats = StatsFactory()
        self.stat = StatFactory(stats=self.stats)

        StatsContent.objects.create_for_placeholder(self.placeholder, stats=self.stats, title='Look at us!')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        stats = response.data['blocks'][0]
        self.assertEqual(stats['type'], 'statistics')
        self.assertEqual(stats['content']['title'], 'Look at us!')
        self.assertEqual(stats['content']['stats'][0]['title'], self.stat.title)
        self.assertEqual(stats['content']['stats'][0]['value'], str(self.stat.value))

    def test_results_quotes(self):
        self.quotes = QuotesFactory()
        self.quote = QuoteFactory(quotes=self.quotes)

        QuotesContent.objects.create_for_placeholder(self.placeholder, quotes=self.quotes)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        quotes = response.data['blocks'][0]
        self.assertEqual(quotes['type'], 'quotes')
        self.assertEqual(quotes['content']['quotes'][0]['name'], self.quote.name)
        self.assertEqual(quotes['content']['quotes'][0]['quote'], self.quote.quote)

    def test_results_results(self):
        survey = SurveyFactory.create()

        ResultsContent.objects.create_for_placeholder(self.placeholder, survey=survey)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        survey = response.data['blocks'][0]
        self.assertEqual(survey['type'], 'survey')
        self.assertTrue('response_count' in survey['content'])
        self.assertEqual(survey['content']['answers'], [])

    def test_results_list(self):
        survey = SurveyFactory.create()
        ResultsContent.objects.create_for_placeholder(self.placeholder, survey=survey)

        self.quotes = QuotesFactory()
        self.quote = QuoteFactory(quotes=self.quotes)
        QuotesContent.objects.create_for_placeholder(self.placeholder, quotes=self.quotes)

        self.stats = StatsFactory()
        self.stat = StatFactory(stats=self.stats)
        StatsContent.objects.create_for_placeholder(self.placeholder, stats=self.stats)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data['blocks']), 3)
        self.assertEquals(response.data['blocks'][0]['type'], 'survey')
        self.assertEquals(response.data['blocks'][1]['type'], 'quotes')
        self.assertEquals(response.data['blocks'][2]['type'], 'statistics')
