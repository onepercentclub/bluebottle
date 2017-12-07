# coding=utf-8
import os

from django.core import mail
from django.test.utils import override_settings
from django.conf import settings

from tenant_schemas.urlresolvers import reverse

from bluebottle.members.models import CustomMemberFieldSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
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


@override_settings(SEND_WELCOME_MAIL=False)
class MemberAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(MemberAdminTest, self).setUp()

        self.member_url = reverse('admin:members_member_add')
        self.client.force_login(self.superuser)

    def test_form(self):
        response = self.client.get(self.member_url)
        self.assertIn('Add member', response.content)

    def test_invalid_form(self):
        response = self.client.get(self.member_url)
        csrf = self.get_csrf_token(response)
        data = {
            'csrfmiddlewaretoken': csrf
        }
        response = self.client.post(self.member_url, data)
        self.assertIn('Please correct the errors below.', response.content)

    @override_settings(
        SEND_WELCOME_MAIL=True,
        MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test',
                                      'properties'))
    def test_valid_form(self):
        response = self.client.get(self.member_url)
        csrf = self.get_csrf_token(response)
        data = {
            'email': 'bob@bob.com',
            'first_name': 'Bob',
            'last_name': 'Bob',
            'csrfmiddlewaretoken': csrf
        }
        response = self.client.post(self.member_url, data)
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.com'])
        self.assertTrue('Set password' in welcome_email.body)
        self.assertTrue('test@example.com' in welcome_email.body,
                        'Tenant contact email should be present.')


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


class MemberCustomFieldAdminTest(BluebottleAdminTestCase):
    """
    Test extra fields in Member Admin
    """

    def setUp(self):
        super(MemberCustomFieldAdminTest, self).setUp()
        self.client.force_login(self.superuser)

    def test_save_custom_fields(self):
        member = BlueBottleUserFactory.create()
        field = CustomMemberFieldSettings.objects.create(name='Department')
        member.extra.create(value='Engineering', field=field)
        member.save()

        member_url = reverse('admin:members_member_change', args=(member.id, ))
        response = self.client.get(member_url)
        self.assertEqual(response.status_code, 200)
        # Test the extra field and it's value show up
        self.assertContains(response, 'Department')
        self.assertContains(response, 'Engineering')
