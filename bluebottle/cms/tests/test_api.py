from builtins import range
from builtins import str

from django.contrib.auth.models import Permission, Group
from django.core.files.base import File
from django.urls import reverse
from django.utils.timezone import now
from fluent_contents.models import Placeholder
from fluent_contents.plugins.rawhtml.models import RawHtmlItem
from fluent_contents.plugins.text.models import TextItem

from bluebottle.cms.models import (
    QuotesContent, PeopleContent,
    HomePage, SlidesContent, SitePlatformSettings,
    LinksContent, StepsContent, HomepageStatisticsContent, LogosContent,
    CategoriesContent, PlainTextItem, ImagePlainTextItem, ImageItem
)
from bluebottle.contentplugins.models import PictureItem
from bluebottle.initiatives.tests.test_api import get_include
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.pages.models import DocumentItem, ImageTextItem
from bluebottle.statistics.tests.factories import ManualStatisticFactory
from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.cms import (
    HomePageFactory, StepFactory,
    SlideFactory
)
from bluebottle.test.factory_models.news import NewsItemFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase, APITestCase


class NewsItemTestCase(BluebottleTestCase):
    """
    Test the news cms endpoint.
    """

    def setUp(self):
        super(NewsItemTestCase, self).setUp()
        self.init_projects()
        self.news_item = NewsItemFactory.create(slug='new-news', language='en')
        self.placeholder = self.news_item.contents
        self.url = reverse('news-detail', args=(self.news_item.slug, ))

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
        data = response.json()['data']
        self.assertEqual(data['attributes']['title'], self.news_item.title)
        self.assertEqual(
            data['relationships']['author']['data']['id'], str(self.news_item.author.pk)
        )
        self.assertTrue(data['attributes']['main-image'].startswith('/media/cache'))
        self.assertEqual(
            data['relationships']['blocks']['data'][0]['type'], 'pages/blocks/raw-html'
        )


class HomeTestCase(APITestCase):
    """
    Integration tests for the Home API.
    """
    model = HomePage

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
            {'id': str(stat.pk), 'type': 'pages/blocks/stats'}
        )

        stats_block = get_include(response, 'pages/blocks/stats')
        self.assertEqual(
            stats_block['relationships']['stats']['links']['related'],
            '/api/statistics/list?'
        )

    def test_stats_with_year(self):
        block = HomepageStatisticsContent.objects.create_for_placeholder(self.placeholder)
        block.year = '2023'
        block.save()
        ManualStatisticFactory.create(name='Trees planted', value=250, icon='trees')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': str(block.pk), 'type': 'pages/blocks/stats'}
        )

        stats_block = get_include(response, 'pages/blocks/stats')
        self.assertEqual(
            stats_block['relationships']['stats']['links']['related'],
            '/api/statistics/list?&year=2023'
        )

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
            {'id': str(block.pk), 'type': 'pages/blocks/steps'}
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
            {'id': str(block.pk), 'type': 'pages/blocks/quotes'}
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

    def test_people(self):
        block = PeopleContent.objects.create_for_placeholder(self.placeholder)
        block.persons.create(name='Ik zelf', email="test@example.com", role="developer")
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['relationships']['blocks']['data'][0],
            {'id': str(block.pk), 'type': 'pages/blocks/people'}
        )

        quotes_block = get_include(response, 'pages/blocks/people')
        self.assertEqual(quotes_block['relationships']['persons']['meta']['count'], 1)

        quote = get_include(response, 'pages/blocks/people/persons')

        self.assertEqual(
            quote['attributes']['name'],
            'Ik zelf'
        )
        self.assertEqual(
            quote['attributes']['role'],
            'developer'
        )
        self.assertEqual(
            quote['attributes']['email'],
            'test@example.com'
        )

    def test_logos(self):
        block = LogosContent.objects.create_for_placeholder(self.placeholder)
        block.logos.create(link='http://google.com')
        block.logos.create(link='http://facebook.com')
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'pages/blocks/logos')

        logos_block = get_include(response, 'pages/blocks/logos')
        self.assertEqual(logos_block['relationships']['logos']['meta']['count'], 2)

        logo = get_include(response, 'pages/blocks/logos/logos')

        self.assertEqual(
            logo['attributes']['link'],
            'http://google.com'
        )
        self.assertEqual(
            logo['attributes']['open-in-new-tab'],
            True
        )

    def test_links(self):
        block = LinksContent.objects.create_for_placeholder(self.placeholder)
        block.links.create(action_link='/iniitiatives/overview', action_text='Stay')
        block.links.create(action_link='http://facebook.com', action_text='Away', open_in_new_tab=True)
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'pages/blocks/links')

        links_block = get_include(response, 'pages/blocks/links')
        self.assertEqual(links_block['relationships']['links']['meta']['count'], 2)

        link = get_include(response, 'pages/blocks/links/links')

        self.assertEqual(
            link['attributes']['action-link'],
            '/iniitiatives/overview'
        )
        self.assertEqual(
            link['attributes']['open-in-new-tab'],
            False
        )

    def test_categories(self):
        categories = CategoryFactory.create_batch(3)
        block = CategoriesContent.objects.create_for_placeholder(self.placeholder)
        block.categories.set(categories)
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'pages/blocks/categories')

        categories_block = get_include(response, 'pages/blocks/categories')
        self.assertEqual(categories_block['relationships']['categories']['meta']['count'], 3)

    def test_slides(self):
        SlidesContent.objects.create_for_placeholder(self.placeholder)

        for i in range(0, 3):
            SlideFactory(
                sequence=i,
                publication_date=now(),
                status='published',
                language='en'
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['blocks'][0]['type'], 'pages/blocks/slides')

        slides_block = get_include(response, 'pages/blocks/slides')
        self.assertEqual(len(slides_block['relationships']['slides']['data']), 3)

    def test_plain_text(self):
        block = PlainTextItem.objects.create_for_placeholder(self.placeholder)
        block.text = "To <b>boldly</b> go were no man has gone before!"
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        text_block = get_include(response, 'pages/blocks/plain-text')

        self.assertEqual(
            text_block['type'],
            'pages/blocks/plain-text'
        )

        self.assertEqual(
            text_block['attributes']['text'],
            "To <b>boldly</b> go were no man has gone before!"
        )

    def test_plain_text_link(self):
        block = PlainTextItem.objects.create_for_placeholder(self.placeholder)
        block.text = "To <a href='javascript:alert(\"Owned!\")'>link</a> to the dark side!"
        block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        text_block = get_include(response, 'pages/blocks/plain-text')

        self.assertEqual(
            text_block['type'],
            'pages/blocks/plain-text'
        )

        self.assertEqual(
            text_block['attributes']['text'],
            "To <a>link</a> to the dark side!"
        )

    def test_plain_text_image(self):
        block = ImagePlainTextItem.objects.create_for_placeholder(self.placeholder)
        block.text = "To <b>boldly</b> go were no man has gone before!"
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            block.image = File(f)
            block.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        text_block = get_include(response, 'pages/blocks/plain-text-image')

        self.assertEqual(
            text_block['type'],
            'pages/blocks/plain-text-image'
        )

        self.assertEqual(
            text_block['attributes']['text'],
            "To <b>boldly</b> go were no man has gone before!"
        )
        self.assertIsNotNone(
            text_block['attributes']['image']['full']
        )
        self.assertEqual(
            text_block['attributes']['ratio'],
            "0.5"
        )
        self.assertEqual(
            text_block['attributes']['align'],
            "right"
        )

    def test_image(self):
        block = ImageItem.objects.create_for_placeholder(self.placeholder)
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            block.image = File(f)
            block.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        text_block = get_include(response, 'pages/blocks/image')

        self.assertEqual(
            text_block['type'],
            'pages/blocks/image'
        )

        self.assertIsNotNone(
            text_block['attributes']['image']['full']
        )

    def test_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_closed_user(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, 200)

    def test_closed_partner(self):
        group = Group.objects.get(name='Authenticated')
        try:
            for permission in Permission.objects.filter(
                codename='api_read_{}'.format(self.model._meta.model_name)
            ):
                group.permissions.remove(
                    permission
                )
        except Permission.DoesNotExist:
            pass
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, 403)


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
        RawHtmlItem.objects.create_for_placeholder(self.placeholder, html='<p>Test content</p>')
        TextItem.objects.create_for_placeholder(self.placeholder, text='<p>Test content</p>')

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            DocumentItem.objects.create_for_placeholder(
                self.placeholder,
                document=image,
                text='Some file upload'
            )

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            PictureItem.objects.create_for_placeholder(
                self.placeholder,
                image=image,
                align='center'
            )

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as f:
            image = File(f)
            ImageTextItem.objects.create_for_placeholder(
                self.placeholder,
                image=image,
                text='some text',
                align='center'
            )

        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='en')

        self.assertEqual(response.status_code, 200)

        data = response.json()['data']

        self.assertEqual(data['attributes']['title'], self.page.title)
        self.assertEqual(data['attributes']['full-page'], self.page.full_page)

        self.assertEqual(
            data['relationships']['blocks']['data'][0]['type'], 'pages/blocks/raw-html'
        )
        self.assertEqual(
            data['relationships']['blocks']['data'][1]['type'], 'pages/blocks/text'
        )
        self.assertEqual(
            data['relationships']['blocks']['data'][2]['type'], 'pages/blocks/document'
        )
        self.assertEqual(
            data['relationships']['blocks']['data'][3]['type'], 'pages/blocks/picture'
        )
        self.assertEqual(
            data['relationships']['blocks']['data'][4]['type'], 'pages/blocks/image-text'
        )

    def test_multi_language_page(self):
        # Should default to main language
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')

        data = response.json()['data']
        self.assertEqual(data['attributes']['title'], 'About us')

        # If we do have a Dutch page, it shoudl return that
        page = PageFactory.create(language='nl', slug='about', title='Over ons')
        Placeholder.objects.create_for_object(page, slot='blog_contents')
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')

        data = response.json()['data']
        self.assertEqual(data['attributes']['title'], 'Over ons')


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
