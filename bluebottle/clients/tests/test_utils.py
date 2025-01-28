from builtins import next

from mock import patch

from bluebottle.clients.utils import get_user_site_links
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory, GroupFactory
from bluebottle.test.factory_models.cms import (
    SiteLinksFactory, LinkFactory, LinkGroupFactory
)
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.models import Language


def _group_by_name(results, name):
    groups = results['groups']
    return next((group for group in groups if group['name'] == name))


class TestSiteLinks(BluebottleTestCase):
    def setUp(self):
        super(TestSiteLinks, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        language_en = LanguageFactory.create(code='en')
        self.site_links = SiteLinksFactory.create(language=language_en)
        self.link_groups = {}

        self._add_link(title='About us', link='/pages/about')
        self._add_link(title='Task List', link='/initiatives/activities/list')
        self._add_link(group_name='about', title='Search', open_in_new_tab=True, link='https://duck.example.com')

    def _add_link(self, group_name='main', **kwargs):
        if group_name not in self.link_groups:
            self.link_groups[group_name] = LinkGroupFactory.create(title='{} Group'.format(group_name), name=group_name,
                                                                   site_links=self.site_links)

        return LinkFactory.create(link_group=self.link_groups[group_name], **kwargs)

    def test_user_site_links_response(self):
        results = get_user_site_links(self.user1)

        main = _group_by_name(results, 'main')
        main_links = main['links']
        self.assertEqual(len(main_links), 2)
        self.assertEqual(len(_group_by_name(results, 'about')['links']), 1)

        link1 = main_links[0]
        expected1 = {
            'link': '/pages/about',
            'isHighlighted': False,
            'openInNewTab': False,
            'title': 'About us',
            'sequence': 1
        }
        self.assertEqual(main['title'], 'main Group')
        self.assertEqual(link1, expected1)

    def test_user_site_links_external(self):
        results = get_user_site_links(self.user1)

        link = _group_by_name(results, 'about')['links'][0]
        self.assertTrue(link['openInNewTab'])

    def test_user_site_links_group(self):
        secret_link = self._add_link(title='Results Page', link='results')
        partners = GroupFactory.create(name='partners')
        secret_link.groups.add(partners)

        results = get_user_site_links(self.user1)
        self.assertEqual(len(_group_by_name(results, 'main')['links']), 2)

        partners.user_set.add(self.user1)
        results = get_user_site_links(self.user1)
        self.assertEqual(len(_group_by_name(results, 'main')['links']), 3)

    @patch('bluebottle.utils.models.get_language')
    def test_language_language_fallback(self, mock_get_language):
        mock_get_language.return_value = 'nl'

        # Test fallback to first site links when none found for language
        results = get_user_site_links(self.user1)
        self.assertEqual(len(_group_by_name(results, 'main')['links']), 2)

        # Now create NL site links
        language_nl = Language.objects.get(code='nl')
        site_links = SiteLinksFactory.create(language=language_nl)
        link_group = LinkGroupFactory.create(title='NL Group', name='main-nl',
                                             site_links=site_links)
        LinkFactory.create(link_group=link_group, title='Project List NL', link='/initiatives/link')

        # Test language specific site links are loaded if available
        results = get_user_site_links(self.user1)
        links = _group_by_name(results, 'main-nl')['links']
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['title'], 'Project List NL')
