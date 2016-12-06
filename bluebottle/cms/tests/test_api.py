from datetime import timedelta
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from rest_framework import status
from fluent_contents.models import Placeholder

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.cms.models import (
    StatsContent, QuotesContent, SurveyContent, ProjectsContent,
    ProjectImagesContent)

from bluebottle.test.factory_models.surveys import SurveyFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.cms import (
    ResultPageFactory, StatFactory, StatsFactory,
    QuotesFactory, QuoteFactory, ProjectsFactory
)
from bluebottle.test.utils import BluebottleTestCase


class ResultPageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(ResultPageTestCase, self).setUp()
        self.init_projects()

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

    def test_results_projects(self):
        self.project = ProjectFactory()
        self.projects = ProjectsFactory()
        self.projects.projects.add(self.project)

        ProjectsContent.objects.create_for_placeholder(self.placeholder, projects=self.projects)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        projects = response.data['blocks'][0]
        self.assertEqual(projects['type'], 'projects')
        self.assertEqual(projects['content']['projects'][0]['title'], self.project.title)

    def test_results_project_images(self):
        yesterday = now() - timedelta(days=1)
        done_complete = ProjectPhase.objects.get(slug='done-complete')
        ProjectFactory(campaign_ended=yesterday, status=done_complete)
        ProjectFactory(campaign_ended=yesterday, status=done_complete)

        ProjectImagesContent.objects.create_for_placeholder(self.placeholder, title='Nice pics')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        images = response.data['blocks'][0]
        self.assertEqual(images['type'], 'project_images')
        self.assertEqual(images['content']['title'], 'Nice pics')
        self.assertEqual(len(images['content']['images']), 2)

    def test_results_survey(self):
        survey = SurveyFactory.create()

        SurveyContent.objects.create_for_placeholder(self.placeholder, survey=survey)

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
        SurveyContent.objects.create_for_placeholder(self.placeholder, survey=survey)

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
