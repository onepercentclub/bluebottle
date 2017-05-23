from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase


class GroupAdminTest(BluebottleAdminTestCase):

    def setUp(self):
        super(GroupAdminTest, self).setUp()
        self.group_url = reverse('admin:auth_group_change', args=(1,))

    def test_prepare(self):
        response = self.app.get(self.group_url, user=self.superuser)
        self.assertEqual(response.status_code, 200)
