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
        u'model': u'HomePage',
        u'data': [
            {
                u'fields': {
                    u'language_code': u'en',
                    u'sort_order': 1,
                    u'sub_title': None,
                    u'title': None
                },
                u'model': u'SlidesContent',
                u'app': u'cms',
                u'items': []
            }, {
                u'fields': {
                    u'action_text': u'Start your own project',
                    u'title': None,
                    u'action_link': u'/start-project',
                    u'sub_title': None,
                    u'sort_order': 2,
                    u'language_code': u'en'
                },
                u'model': u'StepsContent',
                u'app': u'cms',
                u'items': [
                    {
                        u'model': u'Step',
                        u'data': {
                            u'text': u'Go!',
                            u'image': u'',
                            u'header': u'First',
                            u'sequence': 1
                        },
                        u'app': u'cms'
                    }, {
                        u'model': u'Step',
                        u'data': {
                            u'text': u'Go!',
                            u'image': u'',
                            u'header': u'Second',
                            u'sequence': 2
                        },
                        u'app': u'cms'
                    }, {
                        u'model': u'Step',
                        u'data': {
                            u'text': u'Go!',
                            u'image': u'',
                            u'header': u'Third',
                            u'sequence': 3
                        },
                        u'app': u'cms'
                    }
                ]
            }
        ],
        u'app': u'cms',
        u'properties': {}
    }, {
        u'model': u'Page',
        u'data': [
            {
                u'fields': {
                    u'text': u'A really engaging text!',
                    u'text_final': None,
                    u'sort_order': 1,
                    u'language_code': u'en'
                },
                u'model': u'TextItem',
                u'app': u'text',
                u'items': []
            }
        ],
        u'app': u'pages',
        u'properties': {
            u'status': u'published',
            u'language': u'en',
            u'title': u'About this platform',
            u'publication_date': '2020-01-01 00:00',
            u'slug': u'about',
            u'full_page': False
        }
    }
]
LINK_DUMP = [
    {
        u'language': u'en',
        u'groups': [{
            u'title': u'Main',
            u'name': u'main',
            u'links': [
                {
                    u'component_id': None,
                    u'title': u'Start your initiative',
                    u'component': u'initiatives.start',
                    u'external_link': None,
                    u'highlight': False,
                    u'link_order': 1
                }, {
                    u'component_id': u'about',
                    u'title': u'About this platform',
                    u'component': u'pages',
                    u'external_link': None,
                    u'highlight': False,
                    u'link_order': 2
                },
                {
                    u'component_id': None,
                    u'title': u'',
                    u'component': None,
                    u'external_link': u'https://example.com',
                    u'highlight': False,
                    u'link_order': 3
                }
            ],
            u'group_order': 1
        }, {
            u'title': u'Info',
            u'name': u'info',
            u'links': [
                {
                    u'component_id': u'story',
                    u'title': u'Our story',
                    u'component': u'pages',
                    u'external_link': None,
                    u'highlight': False,
                    u'link_order': 4
                }, {
                    u'component_id': u'how-it-works',
                    u'title': u'How it works',
                    u'component': u'pages',
                    u'external_link': None,
                    u'highlight': False,
                    u'link_order': 5
                }
            ],
            u'group_order': 2
        }],
        u'has_copyright': True
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
        json_file = open("test_pages.json", "r")
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
        json_file = open("test_links.json", "r")
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
