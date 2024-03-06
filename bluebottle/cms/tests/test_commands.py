import json

from django.core.management import call_command
from fluent_contents.plugins.text.models import TextItem
from fluent_contents.tests.factories import create_content_item, create_placeholder

from bluebottle.cms.models import HomePage, SlidesContent, StepsContent, Step, SiteLinks, LinkGroup, Link
from bluebottle.pages.models import Page
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.models import Language

PAGE_DUMP = [{
    'model': 'HomePage',
    'app': 'cms',
    'properties': {},
    'data': [{
        'model': 'SlidesContent',
        'app': 'cms',
        'fields': {
            'language_code': 'en',
            'sort_order': 1,
            'title': None,
            'sub_title': None,
        },
        'items': [],
    }, {
        'model': 'StepsContent',
        'app': 'cms',
        'fields': {
            'language_code': 'en',
            'sort_order': 2,
            'title': None,
            'sub_title': None,
            'action_text': 'Start your own project',
            'action_link': '/start-project',
        },
        'items': [{'model': 'Step', 'app': 'cms', 'data': {
            'image': '',
            'header': 'First',
            'text': 'Go!',
            'link': None,
            'link_text': None,
            'external': False,
            'sequence': 1,
        }}, {'model': 'Step', 'app': 'cms', 'data': {
            'image': '',
            'header': 'Second',
            'text': 'Go!',
            'link': None,
            'link_text': None,
            'external': False,
            'sequence': 2,
        }}, {'model': 'Step', 'app': 'cms', 'data': {
            'image': '',
            'header': 'Third',
            'text': 'Go!',
            'link': None,
            'link_text': None,
            'external': False,
            'sequence': 3,
        }}],
    }],
}, {
    'model': 'Page',
    'app': 'pages',
    'properties': {
        'title': 'About this platform',
        'slug': 'about',
        'status': 'published',
        'language': 'en',
        'full_page': False,
        'publication_date': '2020-01-01 00:00',
    },
    'data': [{
        'model': 'TextItem',
        'app': 'text',
        'fields': {
            'language_code': 'en',
            'sort_order': 1,
            'text': 'A really engaging text!',
            'text_final': None,
        },
        'items': [],
    }],
}]


LINK_DUMP = [
    {
        'language': 'en',
        'groups': [{
            'title': 'Main',
            'name': 'main',
            'links': [
                {
                    'title': 'Start your initiative',
                    'link': '/initiatives/start',
                    'open_in_new_tab': False,
                    'highlight': False,
                    'link_order': 1
                }, {
                    'title': 'About this platform',
                    'link': '/pages/about',
                    'open_in_new_tab': False,
                    'highlight': False,
                    'link_order': 2
                },
                {
                    'title': 'Example',
                    'link': 'https://example.com',
                    'open_in_new_tab': True,
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
                    'title': 'Our story',
                    'link': '/pages/story',
                    'open_in_new_tab': False,
                    'highlight': False,
                    'link_order': 4
                }, {
                    'title': 'How it works',
                    'link': '/pages/how-it-works',
                    'open_in_new_tab': False,
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
        with open("test_pages.json", "r") as json_file:
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
            link='/initiatives/start',
            title='Start your initiative',
            link_group=lg
        )
        Link.objects.create(
            link='/pages/about',
            title='About this platform',
            link_group=lg
        )
        Link.objects.create(
            title='Example',
            link='https://example.com',
            open_in_new_tab=True,
            link_group=lg
        )

        lg = LinkGroup.objects.create(
            name='info',
            title='Info',
            site_links=sl
        )
        Link.objects.create(
            link='/pages/story',
            title='Our story',
            link_group=lg
        )
        Link.objects.create(
            link='/pages/how-it-works',
            title='How it works',
            link_group=lg
        )

        call_command('dumplinks', '-f', 'test_links.json')
        with open("test_links.json", "r") as json_file:
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

        self.assertEqual(groups[0].links.first().link, '/initiatives/start')
