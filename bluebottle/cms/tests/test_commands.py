import json

from django.core.management import call_command
from fluent_contents.plugins.text.models import TextItem
from fluent_contents.tests.factories import create_content_item, create_placeholder

from bluebottle.cms.models import HomePage, SlidesContent, StepsContent, Step, SiteLinks, LinkGroup, Link
from bluebottle.pages.models import Page
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.models import Language

PAGE_DUMP = [
    {
        'model': 'HomePage',
        'data': [
            {
                'fields': {
                    'language_code': 'en',
                    'sort_order': 1,
                    'sub_title': None,
                    'title': None
                },
                'model': 'SlidesContent',
                'app': 'cms',
                'items': []
            }, {
                'fields': {
                    'action_text': 'Start your own project',
                    'title': None,
                    'action_link': '/start-project',
                    'sub_title': None,
                    'sort_order': 2,
                    'language_code': 'en'
                },
                'model': 'StepsContent',
                'app': 'cms',
                'items': [
                    {
                        'model': 'Step',
                        'data': {
                            'text': 'Go!',
                            'image': '',
                            'header': 'First',
                            'sequence': 1
                        },
                        'app': 'cms'
                    }, {
                        'model': 'Step',
                        'data': {
                            'text': 'Go!',
                            'image': '',
                            'header': 'Second',
                            'sequence': 2
                        },
                        'app': 'cms'
                    }, {
                        'model': 'Step',
                        'data': {
                            'text': 'Go!',
                            'image': '',
                            'header': 'Third',
                            'sequence': 3
                        },
                        'app': 'cms'
                    }
                ]
            }
        ],
        'app': 'cms',
        'properties': {}
    }, {
        'model': 'Page',
        'data': [
            {
                'fields': {
                    'text': 'A really engaging text!',
                    'text_final': None,
                    'sort_order': 1,
                    'language_code': 'en'
                },
                'model': 'TextItem',
                'app': 'text',
                'items': []
            }
        ],
        'app': 'pages',
        'properties': {
            'status': 'published',
            'language': 'en',
            'title': 'About this platform',
            'publication_date': '2020-01-01 00:00',
            'slug': 'about',
            'full_page': False
        }
    }
]
LINK_DUMP = [
    {
        'language': 'en',
        'groups': [{
            'title': 'Main',
            'name': 'main',
            'links': [
                {
                    'component_id': None,
                    'title': 'Start your initiative',
                    'component': 'initiatives.start',
                    'external_link': None,
                    'highlight': False,
                    'link_order': 1
                }, {
                    'component_id': 'about',
                    'title': 'About this platform',
                    'component': 'pages',
                    'external_link': None,
                    'highlight': False,
                    'link_order': 2
                },
                {
                    'component_id': None,
                    'title': '',
                    'component': None,
                    'external_link': 'https://example.com',
                    'highlight': False,
                    'link_order': 3
                }
            ],
            'group_order': 1
        }, {
            'title': 'Info',
            'name': 'info',
            'links': [
                {
                    'component_id': 'story',
                    'title': 'Our story',
                    'component': 'pages',
                    'external_link': None,
                    'highlight': False,
                    'link_order': 4
                }, {
                    'component_id': 'how-it-works',
                    'title': 'How it works',
                    'component': 'pages',
                    'external_link': None,
                    'highlight': False,
                    'link_order': 5
                }
            ],
            'group_order': 2
        }],
        'has_copyright': True
    }
]


class PageDumpCommandsTestCase(BluebottleTestCase):

    def test_dumppages(self):
        HomePage.objects.all().delete()
        homepage = HomePage.objects.create(pk=1)
        placeholder = create_placeholder(page=homepage, slot='content')

        create_content_item(
            SlidesContent,
            placeholder=placeholder,
            sort_order=1,
            language_code='en',
        )

        steps = create_content_item(
            StepsContent,
            placeholder=placeholder,
            sort_order=2,
            language_code='en',
        )

        Step.objects.create(
            block=steps,
            header='First',
            text='Go!',
            sequence=1
        )

        Step.objects.create(
            block=steps,
            header='Second',
            text='Go!',
            sequence=2
        )

        Step.objects.create(
            block=steps,
            header='Third',
            text='Go!',
            sequence=3
        )

        page = PageFactory.create(
            slug='about',
            title='About this platform',
            language='en',
            publication_date='2020-01-01 00:00+00:00'
        )
        create_content_item(
            TextItem,
            create_placeholder(page=page, slot='blog_contents'),
            sort_order=1,
            language_code='en',
            text='A really engaging text!'
        )

        call_command('dumppages', '-f', 'test_pages.json')
        json_file = open("test_pages.json")
        test_output = json.load(json_file)

        self.assertEqual(test_output, PAGE_DUMP)

    def test_loadpages(self):
        with open('test_pages.json', 'w') as f:
            json.dump(PAGE_DUMP, f)

        call_command('loadpages', '-f', 'test_pages.json', '-q')
        homepage = HomePage.objects.get()
        items = homepage.content.get_content_items()
        self.assertEqual(items[0].type, 'slides')
        self.assertEqual(items[1].type, 'steps')
        self.assertEqual(items[1].items.count(), 3)

        page = Page.objects.first()
        items = page.content.get_content_items()
        self.assertEqual(items[0].__class__.__name__, 'TextItem')


class LinkDumpCommandsTestCase(BluebottleTestCase):

    def test_dumplinks(self):
        en = Language.objects.get(code='en')
        sl = SiteLinks.objects.create(language=en)
        lg = LinkGroup.objects.create(
            name='main',
            title='Main',
            site_links=sl
        )
        Link.objects.create(
            component='initiatives.start',
            title='Start your initiative',
            link_group=lg
        )
        Link.objects.create(
            component='pages',
            component_id='about',
            title='About this platform',
            link_group=lg
        )
        Link.objects.create(
            external_link='https://example.com',
            link_group=lg
        )

        lg = LinkGroup.objects.create(
            name='info',
            title='Info',
            site_links=sl
        )
        Link.objects.create(
            component='pages',
            component_id='story',
            title='Our story',
            link_group=lg
        )
        Link.objects.create(
            component='pages',
            component_id='how-it-works',
            title='How it works',
            link_group=lg
        )

        call_command('dumplinks', '-f', 'test_links.json')
        json_file = open("test_links.json")
        test_output = json.load(json_file)

        self.assertEqual(test_output, LINK_DUMP)

    def test_loadlinks(self):
        with open('test_links.json', 'w') as f:
            json.dump(LINK_DUMP, f)

        call_command('loadlinks', '-f', 'test_links.json')
        site_links = SiteLinks.objects.get()
        groups = site_links.link_groups.all()
        self.assertEqual(groups[0].name, 'main')
        self.assertEqual(groups[1].name, 'info')
        self.assertEqual(groups[0].links.count(), 3)
        self.assertEqual(groups[1].links.count(), 2)

        self.assertEqual(groups[0].links.first().component, 'initiatives.start')
