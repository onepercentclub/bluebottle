# coding=utf-8
from tenant_schemas.urlresolvers import reverse

from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.factory_models.projects import ProjectFactory


class GroupAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(GroupAdminTest, self).setUp()
        self.group_url = reverse('admin:auth_group_change', args=(1,))

    def test_prepare(self):
        response = self.app.get(self.group_url, user=self.superuser)
        self.assertEqual(response.status_code, 200)


class InlineModelTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(InlineModelTestCase, self).setUp()

        self.client.force_login(self.superuser)

    def test_inline_votes(self):
        project = ProjectFactory.create(title='A Müller Project')
        vote = VoteFactory.create(voter=self.superuser, project=project)
        member_url = reverse('admin:members_member_change', args=(self.superuser.id,))
        response = self.client.get(member_url)
        self.assertIn(vote.project.title, response.content)
