from django.test.utils import override_settings
from django.urls.base import reverse

from bluebottle.cms.models import Link
from bluebottle.test.factory_models.cms import LinkGroupFactory, LinkFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.test.utils import BluebottleAdminTestCase


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
        # Test that language tabs show (create all we assert on so test is parallel-proof)
        LanguageFactory.create(code='en', language_name='English', native_name='English', default=True)
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        LanguageFactory.create(code='fr', language_name='French', native_name='Français')
        url = reverse('admin:cms_homepage_changelist')

        # Force request language so tabs render consistently
        page = self.app.get(url, extra_environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        tabs = page.html.find('div', {'class': 'parler-language-tabs'})
        self.assertIsNotNone(tabs, 'parler-language-tabs div should be present')
        tabs_text = tabs.text
        self.assertTrue('Dutch' in tabs_text, f'Dutch tab missing; tabs: {tabs_text!r}')
        self.assertTrue('English' in tabs_text, f'English tab missing; tabs: {tabs_text!r}')
        self.assertTrue('French' in tabs_text, f'French tab missing; tabs: {tabs_text!r}')


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
