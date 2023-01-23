import os
from builtins import range
from builtins import str
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission, Group
from django.core.cache import cache
from django.core.files.base import File
from django.urls import reverse
from django.test.utils import override_settings
from django.utils.timezone import now
from fluent_contents.models import Placeholder
from fluent_contents.plugins.rawhtml.models import RawHtmlItem
from fluent_contents.plugins.text.models import TextItem
from moneyed.classes import Money
from rest_framework import status

from bluebottle.cms.models import (
    StatsContent, QuotesContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent, HomePage, SlidesContent, SitePlatformSettings,
    LinksContent, WelcomeContent, StepsContent, ActivitiesContent, HomepageStatisticsContent
)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.initiatives.tests.test_api import get_include
from bluebottle.statistics.tests.factories import ManualStatisticFactory
from bluebottle.time_based.tests.factories import DateActivityFactory
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.pages.models import DocumentItem, ImageTextItem, ActionItem, ColumnsItem
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.cms import (
    ResultPageFactory, HomePageFactory, StatFactory, StepFactory,
    QuoteFactory, SlideFactory, ContentLinkFactory, GreetingFactory,
)
from bluebottle.test.factory_models.news import NewsItemFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase


class ResultPageTestCase(BluebottleTestCase):
    """
    Integration tests for the Results Page API.
    """

    def setUp(self):
        super(ResultPageTestCase, self).setUp()
        self.init_projects()
        with open('./bluebottle/projects/test_images/upload.png', 'rb') as f:
            image = File(f)
            self.page = ResultPageFactory(title='Results last year', image=image)

        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('result-page-detail', kwargs={'pk': self.page.id})
        cache.clear()

    def test_results_header(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Image should come in 4 sizes
        self.assertEqual(len(response.data['image']), 6)
        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

    def test_results_stats(self):
        yesterday = now() - timedelta(days=1)
        long_ago = now() - timedelta(days=365 * 2)
        user = BlueBottleUserFactory(is_co_financer=False)
        funding = FundingFactory(status='open', owner=user)

        DonorFactory.create(
            activity=funding,
            status='succeeded',
            created=yesterday,
            user=user,
            amount=Money(50, 'EUR')
        )
        DonorFactory.create(
            activity=funding,
            status='succeeded',
            created=long_ago,
            user=user,
            amount=Money(50, 'EUR')
        )
        block = StatsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        self.stat1 = StatFactory(type='manual', title='Poffertjes', value=3500, block=block)
        self.stat2 = StatFactory(type='donated_total', title='Donations', value=None, block=block)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data['blocks'][0]
        self.assertEqual(stats['type'], 'statistics')
        self.assertEqual(stats['title'], 'Look at us!')
        self.assertEqual(stats['stats'][0]['title'], self.stat1.title)
        self.assertEqual(stats['stats'][0]['value'], str(self.stat1.value))
        self.assertEqual(stats['stats'][1]['title'], self.stat2.title)
        self.assertEqual(stats['stats'][1]['value'], {"amount": Decimal('50'), "currency": "EUR"})

    def test_results_stats_no_dates(self):
        self.page.start_date = None
        self.page.end_date = None
        self.page.save()

        long_ago = now() - timedelta(days=365 * 2)
        yesterday = now() - timedelta(days=1)
        user = BlueBottleUserFactory(is_co_financer=False)
        funding = FundingFactory(status='open', owner=user)

        DonorFactory.create(
            activity=funding,
            status='succeeded',
            transition_date=yesterday,
            user=user,
            amount=Money(50, 'EUR')
        )
        DonorFactory.create(
            activity=funding,
            status='succeeded',
            transition_date=long_ago,
            user=user,
            amount=Money(50, 'EUR')
        )

        block = StatsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        self.stat1 = StatFactory(type='manual', title='Poffertjes', value=3500, block=block)
        self.stat2 = StatFactory(type='donated_total', title='Donations', value=None, block=block)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data['blocks'][0]
        self.assertEqual(stats['type'], 'statistics')
        self.assertEqual(stats['title'], 'Look at us!')
        self.assertEqual(stats['stats'][0]['title'], self.stat1.title)
        self.assertEqual(stats['stats'][0]['value'], str(self.stat1.value))
        self.assertEqual(stats['stats'][1]['title'], self.stat2.title)
        self.assertEqual(stats['stats'][1]['value'], {"amount": Decimal('100'), "currency": "EUR"})

    def test_results_quotes(self):
        block = QuotesContent.objects.create_for_placeholder(self.placeholder)
        self.quote = QuoteFactory(block=block)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        quotes = response.data['blocks'][0]
        self.assertEqual(quotes['type'], 'quotes')
        self.assertEqual(quotes['quotes'][0]['name'], self.quote.name)
        self.assertEqual(quotes['quotes'][0]['quote'], self.quote.quote)

    def test_results_activities(self):
        DateActivityFactory.create(status='open', highlight=True)
        ActivitiesContent.objects.create_for_placeholder(self.placeholder)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        projects = response.data['blocks'][0]
        self.assertEqual(projects['type'], 'activities')

    def test_results_share_results(self):
        share_text = '{people} donated {donated} and did {tasks} tasks and joined {activities} activities.'
        ShareResultsContent.objects.create_for_placeholder(
            self.placeholder, title='Share', share_text=share_text
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        share = response.data['blocks'][0]
        self.assertEqual(share['type'], 'share-results')
        self.assertEqual(share['title'], 'Share')
        self.assertEqual(share['share_text'], share_text)

        for key in ['people', 'amount', 'hours', 'time', 'fundraisers']:
            self.assertTrue(key in share['statistics'])

    def test_results_map(self):
        ProjectsMapContent.objects.create_for_placeholder(self.placeholder, title='Test title')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['description'], self.page.description)

        data = response.data['blocks'][0]
        self.assertEqual(data['type'], 'projects-map')

    def test_results_list(self):
        quote_block = QuotesContent.objects.create_for_placeholder(self.placeholder)
        self.quote = QuoteFactory(block=quote_block)

        stat_block = StatsContent.objects.create_for_placeholder(self.placeholder)
        self.stat = StatFactory(block=stat_block)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['blocks']), 2)
        self.assertEqual(response.data['blocks'][0]['type'], 'quotes')
        self.assertEqual(response.data['blocks'][1]['type'], 'statistics')

    def test_results_supporters(self):
        yesterday = now() - timedelta(days=1)
        co_financer = BlueBottleUserFactory(is_co_financer=True)
        user = BlueBottleUserFactory(is_co_financer=False)
        funding = FundingFactory(status='open', owner=user)

        DonorFactory.create(
            activity=funding,
            status='succeeded',
            transition_date=yesterday,
            user=user,
            amount=Money(50, 'EUR')
        )
        DonorFactory.create(
            activity=funding,
            status='succeeded',
            transition_date=yesterday,
            user=co_financer,
            amount=Money(50, 'EUR')
        )
        DonorFactory.create(
            activity=funding,
            status='succeeded',
            transition_date=yesterday,
            user=co_financer,
            amount=Money(50, 'EUR')
        )

        SupporterTotalContent.objects.create_for_placeholder(self.placeholder)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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


class OldHomePageTestCase(BluebottleTestCase):
    """
    Integration tests for the Home Page API.
    """

    def setUp(self):
        super(OldHomePageTestCase, self).setUp()
        HomePage.objects.get(pk=1).delete()
        self.page = HomePageFactory(pk=1)
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('home-page-detail')

    def test_homepage(self):
        RawHtmlItem.objects.create_for_placeholder(self.placeholder, html='<p>Test content</p>')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['blocks'][0]['type'], 'raw-html')
        self.assertEqual(response.data['blocks'][0]['html'], '<p>Test content</p>')

    def test_activities_from_homepage(self):
        DateActivityFactory.create_batch(10, status='open', highlight=True)
        ActivitiesContent.objects.create_for_placeholder(self.placeholder)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'activities')

    def test_slides_png(self):
        SlidesContent.objects.create_for_placeholder(self.placeholder)
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

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

        with open('./bluebottle/cms/tests/test_images/upload.svg', 'rb') as f:
            image = File(f)

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
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

            for i in range(0, 4):
                ContentLinkFactory.create(block=block, image=image)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'links')

    def test_action(self):
        block = ActionItem.objects.create_for_placeholder(self.placeholder)
        block.link = '/pages/start'
        block.title = 'Start an initiative'
        block.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'action')
        self.assertEqual(response.data['blocks'][0]['link'], '/pages/start')
        self.assertEqual(response.data['blocks'][0]['title'], 'Start an initiative')

    def test_columns(self):
        block = ColumnsItem.objects.create_for_placeholder(self.placeholder)
        block.text1 = 'Some text'
        block.text2 = 'More text'
        block.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'columns')
        self.assertEqual(response.data['blocks'][0]['text1'], 'Some text')
        self.assertEqual(response.data['blocks'][0]['text2'], 'More text')

    def test_steps(self):
        block = StepsContent.objects.create_for_placeholder(self.placeholder)

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

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

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

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


class NewsItemTestCase(BluebottleTestCase):
    """
    Test the news cms endpoint.
    """

    def setUp(self):
        super(NewsItemTestCase, self).setUp()
        self.init_projects()
        self.news_item = NewsItemFactory.create(slug='new-news', language='en')
        self.placeholder = self.news_item.contents
        self.url = reverse('news-item-detail', args=(self.news_item.slug, ))

    def test_news_item(self):
        html = RawHtmlItem.objects.create_for_placeholder(
            self.placeholder,
            html='<p>Test content</p>'
        )
        self.assertEqual(self.news_item.language, 'en')
        self.assertEqual(self.news_item.status, 'published')
        self.assertGreaterEqual(now(), self.news_item.publication_date)
        self.assertEqual(html.language_code, 'en')

        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='en')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], self.news_item.title)
        self.assertEqual(response.data['language'], self.news_item.language)
        self.assertEqual(response.data['author']['id'], self.news_item.author.pk)
        self.assertEqual(response.data['allow_comments'], self.news_item.allow_comments)
        self.assertTrue(response.data['main_image'].startswith('/media/cache'))
        self.assertEqual(response.data['blocks'][0]['type'], 'raw-html')
        self.assertEqual(response.data['blocks'][0]['html'], html.html)


class HomeTestCase(BluebottleTestCase):
    """
    Integration tests for the Home API.
    """

    def setUp(self):
        super(HomeTestCase, self).setUp()
        HomePage.objects.get(pk=1).delete()
        self.page = HomePageFactory(pk=1)
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        self.url = reverse('home-detail')

    def test_stats(self):
        stat = HomepageStatisticsContent.objects.create_for_placeholder(self.placeholder)
        ManualStatisticFactory.create(name='Trees planted', value=250, icon='trees')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': stat.pk, 'type': 'pages/blocks/stats'}
        )

        stats_block = get_include(response, 'pages/blocks/stats')
        self.assertEqual(stats_block['relationships']['stats']['links']['related'], '/api/statistics/list')

    def test_stats_with_year(self):
        block = HomepageStatisticsContent.objects.create_for_placeholder(self.placeholder)
        block.year = '2023'
        block.save()
        ManualStatisticFactory.create(name='Trees planted', value=250, icon='trees')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': block.pk, 'type': 'pages/blocks/stats'}
        )

        stats_block = get_include(response, 'pages/blocks/stats')
        self.assertEqual(stats_block['relationships']['stats']['links']['related'], '/api/statistics/list?year=2023')

    def test_steps(self):
        block = StepsContent.objects.create_for_placeholder(self.placeholder)
        block.action_text = 'Here you go'
        block.save()
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

            for i in range(0, 4):
                StepFactory.create(
                    block=block,
                    header='test header',
                    text='<a href="http://example.com">link</a>',
                    image=image
                )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': block.pk, 'type': 'pages/blocks/steps'}
        )

        step_block = get_include(response, 'pages/blocks/steps')
        self.assertEqual(step_block['attributes']['action-text'], 'Here you go')

        step = get_include(response, 'pages/blocks/steps/steps')
        self.assertEqual(step['attributes']['header'], 'test header')
        self.assertEqual(step['attributes']['text'], '<a href="http://example.com">link</a>')

    def test_steps_unsafe(self):
        block = StepsContent.objects.create_for_placeholder(self.placeholder)

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)

            StepFactory.create(
                block=block,
                header='test header',
                text='<script src="http://example.com"></script>Some text',
                image=image
            )

        response = self.client.get(self.url)

        step = get_include(response, 'pages/blocks/steps/steps')
        self.assertEqual(
            step['attributes']['text'],
            '&lt;script src="http://example.com"&gt;&lt;/script&gt;Some text'
        )

    def test_quotes(self):
        block = QuotesContent.objects.create_for_placeholder(self.placeholder)
        block.quotes.create(name='Ik zelf', quote="Leuk! Al zeg ik het zelf.")
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': block.pk, 'type': 'pages/blocks/quotes'}
        )

        quotes_block = get_include(response, 'pages/blocks/quotes')
        self.assertEqual(quotes_block['relationships']['quotes']['meta']['count'], 1)

        quote = get_include(response, 'pages/blocks/quotes/quotes')

        self.assertEqual(
            quote['attributes']['name'],
            'Ik zelf'
        )
        self.assertEqual(
            quote['attributes']['quote'],
            'Leuk! Al zeg ik het zelf.'
        )


class PageTestCase(BluebottleTestCase):
    """
    Test the page cms endpoint.
    """

    def setUp(self):
        super(PageTestCase, self).setUp()
        self.init_projects()
        self.page = PageFactory.create(language='en', slug='about', title='About us')
        self.placeholder = Placeholder.objects.create_for_object(self.page, slot='blog_contents')
        self.url = reverse('page-detail', args=(self.page.slug, ))

    def test_page(self):
        html = RawHtmlItem.objects.create_for_placeholder(self.placeholder, html='<p>Test content</p>')
        text = TextItem.objects.create_for_placeholder(self.placeholder, text='<p>Test content</p>')

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            document = DocumentItem.objects.create_for_placeholder(
                self.placeholder,
                document=image,
                text='Some file upload'
            )

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            picture = PictureItem.objects.create_for_placeholder(
                self.placeholder,
                image=image,
                align='center'
            )

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            image_text = ImageTextItem.objects.create_for_placeholder(
                self.placeholder,
                image=image,
                text='some text',
                align='center'
            )

        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='en')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['title'], self.page.title)
        self.assertEqual(response.data['language'], self.page.language)
        self.assertEqual(response.data['full_page'], self.page.full_page)

        self.assertEqual(response.data['blocks'][0]['type'], 'raw-html')
        self.assertEqual(response.data['blocks'][0]['html'], html.html)

        self.assertEqual(response.data['blocks'][1]['type'], 'text')
        self.assertEqual(response.data['blocks'][1]['text'], text.text)

        self.assertEqual(response.data['blocks'][2]['type'], 'document')
        self.assertEqual(
            os.path.basename(response.data['blocks'][2]['document']),
            os.path.basename(document.document.name)
        )

        self.assertEqual(response.data['blocks'][3]['type'], 'image')
        self.assertEqual(response.data['blocks'][3]['align'], picture.align)
        self.assertTrue(
            '/media/cache' in response.data['blocks'][3]['image']['large']
        )

        self.assertEqual(response.data['blocks'][4]['type'], 'image-text')
        self.assertEqual(response.data['blocks'][4]['align'], image_text.align)
        self.assertTrue(
            '/media/cache' in response.data['blocks'][4]['image']['large']
        )

    def test_multi_language_page(self):
        # Should default to main language
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.data['title'], 'About us')
        self.assertEqual(response.data['language'], 'en')

        # If we do have a Dutch page, it shoudl return that
        self.page = PageFactory.create(language='nl', slug='about', title='Over ons')
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.data['title'], 'Over ons')
        self.assertEqual(response.data['language'], 'nl')

    @override_settings(TIME_ZONE='Asia/Krasnoyarsk')
    def test_time_zone(self):
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='en')
        self.assertEqual(response.data['title'], 'About us')
        self.assertEqual(response.data['language'], 'en')


class SitePlatformSettingsTestCase(BluebottleTestCase):
    """
    Integration tests for the SitePlatformSettings API.
    """

    def setUp(self):
        super(SitePlatformSettingsTestCase, self).setUp()
        self.init_projects()

    def test_site_platform_settings_header(self):
        settings = SitePlatformSettings.objects.create(
            contact_email='info@example.com',
            contact_phone='+31207158980',
            copyright='GoodUp',
            powered_by_text='Powered by',
            powered_by_link='https://goodup.com'
        )
        settings.set_current_language('en')
        settings.metadata_title = "Let's do some good!"
        settings.metadata_description = "Join our platform and start fulfilling your purpose!"
        settings.metadata_keywords = "Do-good, Awesome, Purpose"
        settings.set_current_language('nl')
        settings.metadata_title = "Doe es iets goeds!"
        settings.save()

        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['content']['contact_email'], 'info@example.com')
        self.assertEqual(response.data['platform']['content']['contact_phone'], '+31207158980')
        self.assertEqual(response.data['platform']['content']['copyright'], 'GoodUp')
        self.assertEqual(response.data['platform']['content']['powered_by_text'], 'Powered by')
        self.assertEqual(response.data['platform']['content']['powered_by_link'], 'https://goodup.com')
        self.assertEqual(response.data['platform']['content']['metadata_title'], "Let's do some good!")
        self.assertEqual(
            response.data['platform']['content']['metadata_description'],
            "Join our platform and start fulfilling your purpose!"
        )

        response = self.client.get(reverse('settings'), HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.data['platform']['content']['metadata_title'], "Doe es iets goeds!")
        self.assertEqual(response.data['platform']['content']['metadata_description'], None)

    def test_site_platform_settings_favicons(self):
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            favicon = File(f)
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
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            favicon = File(f)
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
