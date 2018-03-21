from datetime import timedelta
from decimal import Decimal

import mock

from django.contrib.auth.models import Permission, Group
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from moneyed.classes import Money

from rest_framework import status
from fluent_contents.models import Placeholder
from fluent_contents.plugins.rawhtml.models import RawHtmlItem

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.cms.models import (
    StatsContent, QuotesContent, SurveyContent, ProjectsContent,
    ProjectImagesContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent, HomePage, SlidesContent, SitePlatformSettings,
    LinksContent, WelcomeContent, StepsContent
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.surveys import SurveyFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.cms import (
    ResultPageFactory, HomePageFactory, StatFactory, StepFactory,
    QuoteFactory, SlideFactory, ContentLinkFactory, GreetingFactory,
)
from bluebottle.test.utils import BluebottleTestCase
from sorl_watermarker.engines.pil_engine import Engine


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
        def watermark(self, image, *args, **kwargs):
            return image

        with mock.patch.object(Engine, 'watermark', side_effect=watermark) as watermark_mock:
            response = self.client.get(self.url)
            self.assertEquals(response.status_code, status.HTTP_200_OK)
            # Image should come in 4 sizes
            self.assertEqual(len(response.data['image']), 4)
            self.assertEqual(response.data['title'], self.page.title)
            self.assertEqual(response.data['description'], self.page.description)
            self.assertEqual(watermark_mock.call_args[0][1]['watermark'], 'test/logo-overlay.png')

    def test_results_stats(self):

        block = StatsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        self.stat1 = StatFactory(type='manual', title='Poffertjes', value=3500, block=block)
        self.stat2 = StatFactory(type='donated_total', title='Donations', value=None, block=block)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        stats = response.data['blocks'][0]
        self.assertEqual(stats['type'], 'statistics')
        self.assertEqual(stats['title'], 'Look at us!')
        self.assertEqual(stats['stats'][0]['title'], self.stat1.title)
        self.assertEqual(stats['stats'][0]['value'], str(self.stat1.value))
        self.assertEqual(stats['stats'][1]['title'], self.stat2.title)
        self.assertEqual(stats['stats'][1]['value'], {"amount": Decimal('0'), "currency": "EUR"})

    def test_results_stats_dates(self):
        self.page.start_date = None
        self.page.end_date = None
        self.page.save()

        block = StatsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        self.stat1 = StatFactory(type='manual', title='Poffertjes', value=3500, block=block)
        self.stat2 = StatFactory(type='donated_total', title='Donations', value=None, block=block)

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
        block = QuotesContent.objects.create_for_placeholder(self.placeholder)
        self.quote = QuoteFactory(block=block)

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
        block = ProjectsContent.objects.create_for_placeholder(self.placeholder)
        block.projects.add(self.project)

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
        ProjectsMapContent.objects.create_for_placeholder(self.placeholder, title='Test title')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        data = response.data['blocks'][0]
        self.assertEqual(data['type'], 'projects-map')

    def test_results_list(self):
        survey = SurveyFactory.create()
        SurveyContent.objects.create_for_placeholder(self.placeholder, survey=survey)

        quote_block = QuotesContent.objects.create_for_placeholder(self.placeholder)
        self.quote = QuoteFactory(block=quote_block)

        stat_block = StatsContent.objects.create_for_placeholder(self.placeholder)
        self.stat = StatFactory(block=stat_block)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data['blocks']), 3)
        self.assertEquals(response.data['blocks'][0]['type'], 'survey')
        self.assertEquals(response.data['blocks'][1]['type'], 'quotes')
        self.assertEquals(response.data['blocks'][2]['type'], 'statistics')

    def test_results_supporters(self):
        yesterday = now() - timedelta(days=1)
        co_financer = BlueBottleUserFactory(is_co_financer=True)
        user = BlueBottleUserFactory(is_co_financer=False)
        project = ProjectFactory(created=yesterday, owner=user)
        order1 = OrderFactory(user=co_financer, confirmed=yesterday, status='success')
        order2 = OrderFactory(user=co_financer, confirmed=yesterday, status='success')
        order3 = OrderFactory(user=user, confirmed=yesterday, status='success')
        DonationFactory(order=order1, amount=Money(50, 'EUR'), project=project)
        DonationFactory(order=order2, amount=Money(50, 'EUR'), project=project)
        DonationFactory(order=order3, amount=Money(50, 'EUR'), project=project)

        SupporterTotalContent.objects.create_for_placeholder(self.placeholder)

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        block = response.data['blocks'][0]
        self.assertEqual(block['type'], 'supporter_total')
        self.assertEqual(len(block['co_financers']), 1)
        self.assertEqual(block['co_financers'][0]['total']['amount'], 100)

    def test_permission(self):
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_resultpage')
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_permission(self):
        user = BlueBottleUserFactory.create()
        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_resultpage')
        )
        response = self.client.get(
            self.url,
            token='JWT {0}'.format(user.get_jwt_token())
        )
        self.assertEqual(response.status_code, 403)


class HomePageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(HomePageTestCase, self).setUp()
        self.init_projects()
        HomePage.objects.get(pk=1).delete()
        self.page = HomePageFactory(pk=1)
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('home-page-detail')

    def test_homepage(self):
        RawHtmlItem.objects.create_for_placeholder(self.placeholder, html='<p>Test content</p>')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['blocks'][0]['type'], 'rawhtmlitem')
        self.assertEqual(response.data['blocks'][0]['content'], 'Test content')

    def test_projects_from_homepage(self):
        done_complete = ProjectPhase.objects.get(slug='done-complete')
        for i in range(0, 5):
            ProjectFactory.create(is_campaign=True, status=done_complete)

        for i in range(0, 5):
            ProjectFactory.create(is_campaign=False, status=done_complete)

        ProjectsContent.objects.create_for_placeholder(self.placeholder, from_homepage=True)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['blocks'][0]['type'], 'projects')
        self.assertEqual(len(response.data['blocks'][0]['projects']), 4)

        for project in response.data['blocks'][0]['projects']:
            self.assertTrue(project['is_campaign'])

    def test_slides(self):
        SlidesContent.objects.create_for_placeholder(self.placeholder)
        image = File(open('./bluebottle/cms/tests/test_images/upload.png'))

        for i in range(0, 4):
            SlideFactory(
                image=image,
                sequence=i,
                publication_date=now(),
                status='published',
                language='en'
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['blocks'][0]['type'], 'slides')
        self.assertEqual(len(response.data['blocks'][0]['slides']), 4)

        for slide in response.data['blocks'][0]['slides']:
            self.assertTrue(slide['image'].startswith('/media'))
            self.assertTrue(slide['image'].endswith('png'))

    def test_slides_svg(self):
        SlidesContent.objects.create_for_placeholder(self.placeholder)
        image = File(open('./bluebottle/cms/tests/test_images/upload.svg'))

        for i in range(0, 4):
            SlideFactory(
                image=image,
                sequence=i,
                publication_date=now(),
                status='published',
                language='en'
            )

        response = self.client.get(self.url)

        self.assertEqual(len(response.data['blocks'][0]['slides']), 4)
        self.assertEqual(response.status_code, 200)

        for slide in response.data['blocks'][0]['slides']:
            self.assertTrue(slide['image'].startswith('/media'))
            self.assertTrue(slide['image'].endswith('svg'))

    def test_map(self):
        ProjectsMapContent.objects.create_for_placeholder(self.placeholder)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'projects-map')

    def test_links(self):
        block = LinksContent.objects.create_for_placeholder(self.placeholder)
        image = File(open('./bluebottle/cms/tests/test_images/upload.svg'))

        for i in range(0, 4):
            ContentLinkFactory.create(block=block, image=image)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'links')

    def test_steps(self):
        block = StepsContent.objects.create_for_placeholder(self.placeholder)
        image = File(open('./bluebottle/cms/tests/test_images/upload.svg'))

        for i in range(0, 4):
            StepFactory.create(
                block=block,
                header='test header',
                text='<a href="http://example.com">link</a>',
                image=image
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'steps')

        for step in response.data['blocks'][0]['steps']:
            self.assertEqual(
                step['text'], u'<a href="http://example.com">link</a>'
            )

    def test_steps_unsafe(self):
        block = StepsContent.objects.create_for_placeholder(self.placeholder)
        image = File(open('./bluebottle/cms/tests/test_images/upload.svg'))

        StepFactory.create(
            block=block,
            header='test header',
            text='<script src="http://example.com"></script>Some text',
            image=image
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'steps')

        for step in response.data['blocks'][0]['steps']:
            self.assertEqual(
                step['text'], u'&lt;script src="http://example.com"&gt;&lt;/script&gt;Some text'
            )

    def test_welcome(self):
        block = WelcomeContent.objects.create_for_placeholder(
            self.placeholder, preamble='Hi')

        greetings = ['Some greeting', 'Another greeting']
        for greeting in greetings:
            GreetingFactory.create(block=block, text='Some greeting')
            GreetingFactory.create(block=block, text='Some greeting')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'welcome')

        block = response.data['blocks'][0]

        self.assertEqual(block['preamble'], 'Hi')
        self.assertTrue(block['greeting'] in greetings)


class SitePlatformSettingsTestCase(BluebottleTestCase):
    """
    Integration tests for the SitePlatformSettings API.
    """

    def setUp(self):
        super(SitePlatformSettingsTestCase, self).setUp()
        self.init_projects()

    def test_site_platform_settings_header(self):
        SitePlatformSettings.objects.create(
            contact_email='info@example.com',
            contact_phone='+31207158980',
            copyright='GoodUp',
            powered_by_text='Powered by',
            powered_by_link='https://goodup.com'
        )

        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['content']['contact_email'], 'info@example.com')
        self.assertEqual(response.data['platform']['content']['contact_phone'], '+31207158980')
        self.assertEqual(response.data['platform']['content']['copyright'], 'GoodUp')
        self.assertEqual(response.data['platform']['content']['powered_by_text'], 'Powered by')
        self.assertEqual(response.data['platform']['content']['powered_by_link'], 'https://goodup.com')

    def test_site_platform_settings_favicons(self):
        favicon = File(open('./bluebottle/projects/test_images/upload.png'))
        SitePlatformSettings.objects.create(favicon=favicon)

        response = self.client.get(reverse('settings'))

        self.assertTrue(
            response.data['platform']['content']['favicons']['large'].startswith(
                '/media/cache'
            )
        )
        self.assertTrue(
            response.data['platform']['content']['favicons']['small'].startswith(
                '/media/cache'
            )
        )

    def test_site_platform_settings_logo(self):
        favicon = File(open('./bluebottle/projects/test_images/upload.png'))
        SitePlatformSettings.objects.create(favicon=favicon)

        response = self.client.get(reverse('settings'))

        self.assertTrue(
            response.data['platform']['content']['favicons']['large'].startswith(
                '/media/cache'
            )
        )
        self.assertTrue(
            response.data['platform']['content']['favicons']['small'].startswith(
                '/media/cache'
            )
        )
