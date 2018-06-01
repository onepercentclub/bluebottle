# coding=utf-8
from bluebottle.bluebottle_dashboard.dashboard import CustomAppIndexDashboard
from bluebottle.projects.dashboard import AppIndexDashboard as ProjectAppIndexDashboard
from django.test.client import RequestFactory
from django.test.utils import override_settings
from jet.dashboard.dashboard import DefaultAppIndexDashboard
from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase


class MainDashboardTest(BluebottleAdminTestCase):
    """
    Test main admin dashboard
    """

    def setUp(self):
        super(MainDashboardTest, self).setUp()
        self.init_projects()
        self.client.force_login(self.superuser)
        self.admin_url = reverse('admin:index')

    def test_main_dashboard(self):
        response = self.client.get(self.admin_url)
        self.assertContains(response, 'Recently submitted project')
        self.assertContains(response, 'Projects nearing deadline')
        self.assertContains(response, 'Recently joined users')
        self.assertContains(response, 'Tasks nearing application deadline')
        self.assertContains(response, 'Export metrics')
        # Stand settings don't show export options
        self.assertNotContains(response, 'Download report')
        self.assertNotContains(response, 'Request complete participation metrics')

    @override_settings(REPORTING_BACKOFFICE_ENABLED=True, PARTICIPATION_BACKOFFICE_ENABLED=True)
    def test_main_dashboard_export_options(self):
        # Override settings to show export options
        response = self.client.get(self.admin_url)
        self.assertContains(response, 'Download report')
        self.assertContains(response, 'Request complete participation metrics')


class CustomAppDashboardTest(BluebottleAdminTestCase):
    """
    Test custom app dashboard loading
    """

    def setUp(self):
        super(CustomAppDashboardTest, self).setUp()
        self.client.force_login(self.superuser)
        self.admin_url = reverse('admin:index')
        self.request = RequestFactory().get(self.admin_url)
        self.request.user = self.superuser

    def test_existing_app_dashboard(self):
        dash = CustomAppIndexDashboard({'request': self.request}, app_label='projects')
        self.assertTrue(isinstance(dash, ProjectAppIndexDashboard))

    def test_non_existing_app_dashboard(self):
        dash = CustomAppIndexDashboard({'request': self.request}, app_label='orders')
        self.assertTrue(isinstance(dash, DefaultAppIndexDashboard))
