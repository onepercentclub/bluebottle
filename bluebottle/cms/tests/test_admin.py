from django.urls.base import reverse
from fluent_contents.models import Placeholder
from django.test.utils import override_settings

from bluebottle.cms.models import StatsContent, ActivitiesContent, Link
from bluebottle.test.factory_models.cms import ResultPageFactory, LinkGroupFactory, LinkFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.test.factory_models.utils import LanguageFactory


class TestResultPageAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestResultPageAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()

    def test_add_results_page(self):
        result_page_url = reverse('admin:cms_resultpage_add')
        response = self.client.get(result_page_url)
        self.assertEqual(response.status_code, 200)

    def test_change_results_page(self):
        result_page = ResultPageFactory.create()
        self.placeholder = Placeholder.objects.create_for_object(result_page, slot='content')
        StatsContent.objects.create_for_placeholder(self.placeholder, title='Look at us!')
        ActivitiesContent.objects.create_for_placeholder(self.placeholder, title='Activities r us!')
        result_page_url = reverse('admin:cms_resultpage_change', args=(result_page.id,))
        response = self.client.get(result_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stats')
        self.assertContains(response, 'Activities')


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    },
)
class HomePageAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)

    def test_admin_language_tabs(self):
        # Test that language tabs show
        LanguageFactory.create(code='fr', language_name='French')
        url = reverse('admin:cms_homepage_changelist')

        page = self.app.get(url)
        tabs = page.html.find('div', {'class': 'parler-language-tabs'})
        self.assertTrue('Dutch' in tabs.text)
        self.assertTrue('English' in tabs.text)
        self.assertTrue('French' in tabs.text)


class SiteLinkAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.link_group = LinkGroupFactory.create()
        LinkFactory.create(link_group=self.link_group)
        self.app.set_user(self.superuser)

    def test_adding_sitelinks(self):
        url = reverse('admin:cms_linkgroup_change', args=(self.link_group.id,))
        PageFactory.create(
            slug='info',
            language=self.link_group.site_links.language.code
        )
        page = self.app.get(url)
        form = page.forms[1]
        form['links-0-title'] = 'Some page'
        form['links-0-link'] = '/pages/some'
        form.submit()

        link = Link.objects.last()
        self.assertEqual(link.link, '/pages/some')
