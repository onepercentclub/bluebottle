import json

from django.core.management import call_command
from fluent_contents.plugins.text.models import TextItem
from fluent_contents.tests.factories import create_content_item, create_placeholder

from bluebottle.cms.models import HomePage, SlidesContent, StepsContent, Step
from bluebottle.pages.models import Page
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleTestCase


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
            u'title': u'Page Title 0',
            u'publication_date': '2020-01-01 00:00',
            u'slug': u'slug-0',
            u'full_page': False
        }
    }
]


class PageDumpCommandsTestCase(BluebottleTestCase):

    def test_dumppages(self):
        self.maxDiff = 1000
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

        page = PageFactory.create(language='en', publication_date='2020-01-01 00:00+00:00')
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

        call_command('loadpages', '-f', 'test_pages.json')
        homepage = HomePage.objects.get()
        items = homepage.content.get_content_items()
        self.assertEqual(items[0].type, 'slides')
        self.assertEqual(items[1].type, 'steps')
        self.assertEqual(len(items[1].items), 3)

        page = Page.objects.first()
        items = page.content.get_content_items()
        self.assertEqual(items[0].type, 'text')
