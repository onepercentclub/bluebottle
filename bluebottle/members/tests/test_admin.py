# coding=utf-8
import os

from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.conf import settings

from tenant_schemas.urlresolvers import reverse

from bluebottle.members.admin import MemberAdmin, MemberChangeForm
from bluebottle.members.models import CustomMemberFieldSettings, Member, CustomMemberField
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase


factory = RequestFactory()


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None, is_staff=True):
        self.perms = perms or []
        self.is_staff = is_staff


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
        self.add_member_url = reverse('admin:members_member_add')
        self.client.force_login(self.superuser)

    def test_form(self):
        response = self.client.get(self.add_member_url)
        self.assertIn('Add member', response.content)

    def test_invalid_form(self):
        response = self.client.get(self.add_member_url)
        csrf = self.get_csrf_token(response)
        data = {
            'csrfmiddlewaretoken': csrf
        }
        response = self.client.post(self.add_member_url, data)
        self.assertIn('Please correct the errors below.', response.content)

    @override_settings(
        SEND_WELCOME_MAIL=True,
        MULTI_TENANT_DIR=os.path.join(settings.PROJECT_ROOT, 'bluebottle', 'test', 'properties'))
    def test_valid_form(self):
        response = self.client.get(self.add_member_url)
        csrf = self.get_csrf_token(response)
        data = {
            'email': 'bob@bob.com',
            'first_name': 'Bob',
            'last_name': 'Bob',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
            'csrfmiddlewaretoken': csrf
        }
        response = self.client.post(self.add_member_url, data)
        self.assertEquals(response.status_code, 302)
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.com'])
        self.assertTrue('Set password' in welcome_email.body)
        self.assertTrue('test@example.com' in welcome_email.body,
                        'Tenant contact email should be present.')

    def test_password_mail(self):
        # Assert password links are shown
        user = BlueBottleUserFactory.create()
        member_url = reverse('admin:members_member_change', args=(user.id,))
        response = self.client.get(member_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Send reset password mail')
        self.assertContains(response, 'Reset password form')

        # Assert password reset link sends the right email
        reset_url = reverse('admin:auth_user_password_reset_mail', kwargs={'user_id': user.id})
        response = self.client.get(reset_url)
        self.assertEquals(response.status_code, 302)
        reset_mail = mail.outbox[0]
        self.assertEqual(reset_mail.to, [user.email])
        self.assertTrue('Please go to the following page and choose a new password' in reset_mail.body)


class MemberCustomFieldAdminTest(BluebottleAdminTestCase):
    """
    Test extra fields in Member Admin
    """

    def setUp(self):
        super(MemberCustomFieldAdminTest, self).setUp()
        self.client.force_login(self.superuser)

    def test_load_custom_fields(self):
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

    def test_save_custom_fields(self):
        member = BlueBottleUserFactory.create()
        CustomMemberFieldSettings.objects.create(name='Department')
        data = member.__dict__
        data['department'] = 'Engineering'
        form = MemberChangeForm(instance=member, data=data)
        form.save()
        member.refresh_from_db()
        self.assertEqual(member.extra.get().value, 'Engineering')


class MemberAdminExportTest(BluebottleTestCase):
    """
    Test csv export
    """
    def setUp(self):
        super(MemberAdminExportTest, self).setUp()
        self.init_projects()
        self.request_factory = RequestFactory()
        self.request = self.request_factory.post('/')
        self.request.user = MockUser()
        self.init_projects()
        self.member_admin = MemberAdmin(Member, AdminSite())

    def test_member_export(self):
        member = BlueBottleUserFactory.create(username='malle-eppie')
        CustomMemberFieldSettings.objects.create(name='Extra Info')
        field = CustomMemberFieldSettings.objects.create(name='How are you')
        CustomMemberField.objects.create(member=member, value='Fine', field=field)

        export_action = self.member_admin.actions[0]
        response = export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.split("\r\n")
        headers = data[0].split(",")
        data = data[1].split(",")

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers[0], 'username')
        self.assertEqual(headers[11], 'Extra Info')
        self.assertEqual(headers[12], 'How are you')
        self.assertEqual(data[0], 'malle-eppie')
        self.assertEqual(data[11], '')
        self.assertEqual(data[12], 'Fine')

    def test_member_unicode_export(self):
        member = BlueBottleUserFactory.create(username='stimpy')
        friend = CustomMemberFieldSettings.objects.create(name='Best friend')
        CustomMemberField.objects.create(member=member, value='Ren Höek', field=friend)

        export_action = self.member_admin.actions[0]
        response = export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.split("\r\n")
        headers = data[0].split(",")
        data = data[1].split(",")

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers[0], 'username')
        self.assertEqual(headers[11], 'Best friend')
        self.assertEqual(data[0], 'stimpy')
        self.assertEqual(data[11], 'Ren Höek')
