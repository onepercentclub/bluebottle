# coding=utf-8
from django.test.client import RequestFactory
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from tenant_schemas.urlresolvers import reverse

from bluebottle.bluebottle_dashboard.dashboard import CustomAppIndexDashboard
from bluebottle.bluebottle_dashboard.tests.factories import UserDashboardModuleFactory
from bluebottle.test.utils import BluebottleAdminTestCase, ApiClient


class MainDashboardTestCase(BluebottleAdminTestCase):
    """
    Test main admin dashboard
    """

    def setUp(self):
        super(MainDashboardTestCase, self).setUp()
        self.init_projects()
        self.client.force_login(self.superuser)
        self.admin_url = reverse('admin:index')

    def test_main_dashboard(self):
        response = self.client.get(self.admin_url)
        self.assertContains(response, 'Recently submitted initiatives')
        self.assertContains(response, 'Recently joined users')
        self.assertContains(response, 'Export metrics')


class CustomAppDashboardTestCase(BluebottleAdminTestCase):
    """
    Test custom app dashboard loading
    """

    def setUp(self):
        super(CustomAppDashboardTestCase, self).setUp()
        self.client.force_login(self.superuser)
        self.admin_url = reverse('admin:index')
        self.request = RequestFactory().get(self.admin_url)
        self.request.user = self.superuser

    def test_non_existing_app_dashboard(self):
        dash = CustomAppIndexDashboard({'request': self.request}, app_label='orders')
        self.assertTrue(isinstance(dash, DefaultAppIndexDashboard))


class DashboardWidgetTestCase(BluebottleAdminTestCase):

    def setUp(self):
        super(DashboardWidgetTestCase, self).setUp()
        self.dashboard = UserDashboardModuleFactory.create(
            title='Links',
            user=self.superuser.id,
            module='jet.dashboard.modules.LinkList'
        )
        self.widget_admin_url = reverse('jet-dashboard:update_module', args=(self.dashboard.id,))

        self.client = ApiClient(self.__class__.tenant, enforce_csrf_checks=True)
        self.client.force_login(self.superuser)

    def test_changing_widget_title_without_csrf(self):
        data = {
            'csrfmiddlewaretoken': 'invalid',
            'title': 'You have been owned!',
            'layout': 'stacked',
            'children-TOTAL_FORMS': 0,
            'children-INITIAL_FORMS': 0,
            '_save': 'Save'
        }

        response = self.client.post(self.widget_admin_url, data, format='multipart')
        self.assertEquals(response.status_code, 403)
        self.dashboard.refresh_from_db()
        self.assertEquals(self.dashboard.title, 'Links')

    def test_changing_widget_title_with_csrf(self):
        response = self.client.get(self.widget_admin_url)
        csrf = self.get_csrf_token(response)
        data = {
            'csrfmiddlewaretoken': csrf,
            'title': 'Nice Links',
            'layout': 'stacked',
            'children-TOTAL_FORMS': 0,
            'children-INITIAL_FORMS': 0,
            '_save': 'Save'
        }
        response = self.client.post(self.widget_admin_url, data, format='multipart')
        self.assertEquals(response.status_code, 302)
        self.dashboard.refresh_from_db()
        self.assertEquals(self.dashboard.title, 'Nice Links')
