# coding=utf-8
from tenant_schemas.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class MemberDashboardTest(BluebottleAdminTestCase):
    """
    Test member admin dashboard
    """

    def setUp(self):
        super(MemberDashboardTest, self).setUp()
        self.client.force_login(self.superuser)
        self.member_admin_url = reverse('admin:app_list', args=('members', ))
        BlueBottleUserFactory.create(username='Cousin Sven')

    def test_member_dashboard(self):

        response = self.client.get(self.member_admin_url)
        self.assertContains(response, 'Recently joined users')
        self.assertContains(response, 'Cousin Sven')
