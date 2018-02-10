# coding=utf-8
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

    def test_project_dashboard(self):
        response = self.client.get(self.admin_url)
        self.assertContains(response, 'Recently submitted project')
        self.assertContains(response, 'Projects nearing deadline')
        self.assertContains(response, 'Recently joined users')
        self.assertContains(response, 'Tasks nearing deadline')
        self.assertContains(response, 'Export metrics')
