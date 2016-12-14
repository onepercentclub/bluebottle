from datetime import timedelta
from decimal import Decimal

from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from rest_framework import status
from fluent_contents.models import Placeholder

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.cms.models import (
    StatsContent, QuotesContent, SurveyContent, ProjectsContent,
    ProjectImagesContent, ShareResultsContent, ProjectsMapContent
)

from bluebottle.test.factory_models.surveys import SurveyFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.cms import (
    ResultPageFactory, StatFactory, StatsFactory, QuotesFactory, QuoteFactory,
    ProjectsFactory
)
from bluebottle.test.utils import BluebottleTestCase


class ResultPageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(ResultPageTestCase, self).setUp()
        self.init_projects()
        image = File(open('./bluebottle/projects/test_images/upload.png'))
        self.page = ResultPageFactory(title='Results last year', image=image)
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('result-page-detail', kwargs={'pk': self.page.id})

    def test_results_header(self):

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # Image should come in 4 sizes
        self.assertEqual(len(response.data['image']), 4)
        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

    def test_results_stats(self):
        self.stats = StatsFactory()
        self.stat1 = StatFactory(stats=self.stats, type='manual', title='Poffertjes', value=3500)
        self.stat2 = StatFactory(stats=self.stats, type='donated_total', title='Donations', value=None)

        StatsContent.objects.create_for_placeholder(self.placeholder, stats=self.stats, title='Look at us!')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        stats = response.data['blocks'][0]
        self.assertEqual(stats['type'], 'statistics')
        self.assertEqual(stats['title'], 'Look at us!')
        self.assertEqual(stats['stats'][0]['title'], self.stat1.title)
        self.assertEqual(stats['stats'][0]['value'], str(self.stat1.value))
        self.assertEqual(stats['stats'][1]['title'], self.stat2.title)
        self.assertEqual(stats['stats'][1]['value'], {"amount": Decimal('0'), "currency": "EUR"})

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
        self.assertEqual(quotes['quotes'][0]['name'], self.quote.name)
        self.assertEqual(quotes['quotes'][0]['quote'], self.quote.quote)

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
        self.assertEqual(projects['projects'][0]['title'], self.project.title)

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
        self.assertEqual(images['title'], 'Nice pics')
        self.assertEqual(len(images['images']), 2)

    def test_results_share_results(self):
        share_text = '{people} donated {donated} to {projects} projects'
        ShareResultsContent.objects.create_for_placeholder(
            self.placeholder, title='Share', share_text=share_text
        )

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        share = response.data['blocks'][0]
        self.assertEqual(share['type'], 'share-results')
        self.assertEqual(share['title'], 'Share')
        self.assertEqual(share['share_text'], share_text)

        for key in ['people', 'amount', 'hours', 'projects', 'tasks', 'votes']:
            self.assertTrue(key in share['statistics'])

    def test_results_survey(self):
        survey = SurveyFactory.create()

        SurveyContent.objects.create_for_placeholder(self.placeholder, survey=survey)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        survey = response.data['blocks'][0]
        self.assertEqual(survey['type'], 'survey')
        self.assertTrue('response_count' in survey)
        self.assertEqual(survey['answers'], [])

    def test_results_map(self):
        done_complete = ProjectPhase.objects.get(slug='done-complete')
        for _index in range(0, 10):
            ProjectFactory.create(campaign_ended=now(), status=done_complete)

        ProjectsMapContent.objects.create_for_placeholder(self.placeholder, title='Test title')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        data = response.data['blocks'][0]
        self.assertEqual(data['type'], 'projects-map')
        self.assertEqual(len(data['projects']), 10)

        project = data['projects'][0]

        for key in ('title', 'slug', 'status', 'image', 'latitude', 'longitude'):
            self.assertTrue(key in project)

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
