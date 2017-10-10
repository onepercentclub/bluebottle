from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.cms import (
    SiteLinksFactory, LinkFactory, LinkPermissionFactory
)
from bluebottle.clients.utils import get_user_site_links


class TestSiteLinks(BluebottleTestCase):
    def setUp(self):
        super(TestSiteLinks, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.site_links = SiteLinksFactory.create()

        self._add_link(title='Some Project', component='project', component_id='some-project')
        self._add_link(title='Task List', component='task')
        self._add_link(title='Search', external_link='https://duckduckgo.com')
        self._add_link(group='about', title='Search', external_link='https://duckduckgo.com')

    def _add_link(self, **kwargs):
        return LinkFactory.create(site_links=self.site_links, **kwargs)

    def test_user_site_links_response(self):
        results = get_user_site_links(self.user1)

        self.assertEqual(len(results['main']), 3)
        self.assertEqual(len(results['about']), 1)

        link1 = results['main'][0]
        expected1 = {
            'route': 'project',
            'isHighlighted': False,
            'param': 'some-project',
            'title': 'Some Project'
        }
        self.assertEqual(link1, expected1)

    def test_user_site_links_perms(self):
        # Add link with resultpage permission
        secret_link = self._add_link(title='Results Page', component='results')
        perm = LinkPermissionFactory.create(permission='cms.api_change_resultpage',
                                            present=True)
        secret_link.link_permissions.add(perm)

        # User can't access link with permissions
        results = get_user_site_links(self.user1)
        self.assertEqual(len(results['main']), 3)

        # Add resultpage permission to User
        resultpage_perm = Permission.objects.get(codename='api_change_resultpage')
        self.user1.user_permissions.add(resultpage_perm)
        self.user1 = get_user_model().objects.get(pk=self.user1.pk)

        # User can now access link with resultpage permission
        results = get_user_site_links(self.user1)
        self.assertEqual(len(results['main']), 4)
