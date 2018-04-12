from urllib import quote_plus
from urlparse import urlparse

from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from django.test.utils import override_settings

from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.test.factory_models.looker import LookerEmbedFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.looker.dashboard import AppIndexDashboard, LookerDashboard


class LookerAppDashboardTest(BluebottleAdminTestCase):
    """
    Test custom app dashboard loading
    """

    def setUp(self):
        super(LookerAppDashboardTest, self).setUp()
        self.client.force_login(self.superuser)
        self.admin_url = reverse('admin:index')
        self.request = RequestFactory().get(self.admin_url)
        self.request.user = self.superuser
        for looker_id in range(3):
            LookerEmbedFactory.create(
                title='Looker Dashboard: {}'.format(looker_id),
                looker_id=looker_id
            )

    def test_app_dashboard(self):
        parent_dashboard = AppIndexDashboard({'request': self.request}, app_label='looker')
        dashboard = parent_dashboard.children[0]
        dashboard.init_with_context({})
        self.assertTrue(isinstance(dashboard, LookerDashboard))
        self.assertEqual(
            len(dashboard.children), 3
        )


@override_settings(LOOKER_HOST='looker.example.com', LOOKER_SECRET='secret')
class LookerEmbedViewTest(BluebottleAdminTestCase):
    """
    Test custom app dashboard loading
    """

    def setUp(self):
        super(LookerEmbedViewTest, self).setUp()
        self.embed = LookerEmbedFactory.create(
            title='Looker Dashboard',
            type='look',
            looker_id=1
        )
        self.target_url = 'https://looker.example.com/login/embed/{}'.format(
            quote_plus('/embed/looks/1')
        )

        self.embed_url = reverse('jet-dashboard:looker-embed', args=(self.embed.pk, ))

    def test_view_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.embed_url)
        self.assertTrue(
            '<iframe src="{}'.format(self.target_url) in response.content
        )
        self.assertTrue(
            'Manage Dashboards' in response.content
        )

    def test_view_permission(self):
        staff_user = BlueBottleUserFactory.create(is_staff=True)
        staff_user.user_permissions.add(
            Permission.objects.get(codename='access_looker_embeds')
        )

        self.client.force_login(staff_user)
        response = self.client.get(self.embed_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            '<iframe src="{}'.format(self.target_url) in response.content
        )

        self.assertFalse(
            'Manage Dashboards' in response.content
        )

    def test_view_not_authenticated(self):
        response = self.client.get(self.embed_url)
        path = urlparse(response['location']).path
        self.assertEqual(path, '/accounts/login/')

    def test_view_no_permission(self):
        staff_user = BlueBottleUserFactory.create(is_staff=True)
        self.client.force_login(staff_user)
        response = self.client.get(self.embed_url)
        self.assertEqual(response.status_code, 403)
