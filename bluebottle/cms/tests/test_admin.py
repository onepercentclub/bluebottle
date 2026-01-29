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
        # Test that language tabs show
        LanguageFactory.create(code='fr', language_name='French')
        url = reverse('admin:cms_homepage_changelist')

        page = self.app.get(url)
        tabs = page.html.find('div', {'class': 'parler-language-tabs'})
        tabs_text = tabs.text.lower()
        self.assertTrue(any(value in tabs_text for value in ('dutch', 'nederlands', 'nl')))
        self.assertTrue(any(value in tabs_text for value in ('english', 'engels', 'en')))
        self.assertTrue(any(value in tabs_text for value in ('french', 'frans', 'fr')))


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
