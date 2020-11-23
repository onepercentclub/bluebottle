# coding=utf-8
from builtins import object
import os

from djmoney.money import Money

from bluebottle.funding.tests.factories import DonorFactory

from bluebottle.assignments.tests.factories import ApplicantFactory

from bluebottle.events.tests.factories import ParticipantFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core import mail
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.conf import settings
from django.utils import timezone

from tenant_schemas.urlresolvers import reverse

from bluebottle.members.admin import MemberAdmin, MemberChangeForm, MemberCreationForm
from bluebottle.members.models import CustomMemberFieldSettings, Member, CustomMemberField
from bluebottle.notifications.models import MessageTemplate
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase
from bluebottle.utils.models import Language

factory = RequestFactory()


class MockRequest(object):
    pass


class MockUser(object):
    def __init__(self, perms=None, is_staff=True, is_superuser=False, groups=None):
        self.perms = perms or []
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        if groups:
            self.groups = groups
        else:
            self.groups = Group.objects.all()


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
        self.assertIn(b'Add member', response.content)

    def test_invalid_form(self):
        response = self.client.get(self.add_member_url)
        csrf = self.get_csrf_token(response)
        data = {
            'csrfmiddlewaretoken': csrf
        }
        response = self.client.post(self.add_member_url, data)
        self.assertIn(b'Please correct the errors below.', response.content)

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
        user = BlueBottleUserFactory.create()
        member_url = reverse('admin:members_member_change', args=(user.id,))
        response = self.client.get(member_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Send reset password mail')

        # Assert password reset link sends the right email
        reset_url = reverse('admin:auth_user_password_reset_mail', kwargs={'pk': user.id})

        confirm_response = self.client.get(reset_url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(b'Are you sure' in confirm_response.content)

        response = self.client.post(reset_url, {'confirm': True})
        self.assertEquals(response.status_code, 302)
        reset_mail = mail.outbox[0]
        self.assertEqual(reset_mail.to, [user.email])
        self.assertTrue('Seems you\'ve requested a password reset for' in reset_mail.body)

    def test_password_mail_anonymous(self):
        user = BlueBottleUserFactory.create()
        self.client.logout()
        reset_url = reverse('admin:auth_user_password_reset_mail', kwargs={'pk': user.id})
        response = self.client.post(reset_url, {'confirm': True})
        self.assertEquals(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_welcome(self):
        user = BlueBottleUserFactory.create(welcome_email_is_sent=True)
        member_url = reverse('admin:members_member_change', args=(user.id,))
        response = self.client.get(member_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Resend welcome email')

        welcome_email_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': user.id})

        confirm_response = self.client.get(welcome_email_url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(b'Are you sure' in confirm_response.content)

        response = self.client.post(welcome_email_url, {'confirm': True})
        self.assertEquals(response.status_code, 302)
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, [user.email])
        self.assertTrue(
            'Welcome {}'.format(user.first_name) in welcome_email.body
        )

    def test_resend_welcome_anonymous(self):
        user = BlueBottleUserFactory.create()
        self.client.logout()

        welkcome_email_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': user.id})
        response = self.client.post(welkcome_email_url, {'confirm': True})
        self.assertEquals(response.status_code, 403)


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
        member = BlueBottleUserFactory.create(password='testing')
        staff = BlueBottleUserFactory.create(is_staff=True)
        CustomMemberFieldSettings.objects.create(name='Department')
        data = member.__dict__
        data['department'] = 'Engineering'
        form = MemberChangeForm(current_user=staff, instance=member, data=data)
        form.save()
        member.refresh_from_db()
        self.assertEqual(member.extra.get().value, 'Engineering')


class MemberFormAdminTest(BluebottleAdminTestCase):
    """
    Test extra fields in Member Admin
    """

    def setUp(self):
        super(MemberFormAdminTest, self).setUp()
        self.client.force_login(self.superuser)
        self.staff = BlueBottleUserFactory.create(is_staff=True)

    def test_save(self):
        data = {
            'email': 'bla@example.com',
            'first_name': 'bla',
            'last_name': 'Example',
            'is_active': True,
            'username': 'bla@example.com',
            'password': 'bla',
            'primary_language': 'en',
            'user_type': 'person',
            'date_joined': timezone.now(),
            'groups': [self.staff.groups.get().pk]
        }
        form = MemberCreationForm(current_user=self.staff, data=data)
        form.save()

        member = Member.objects.get(email='bla@example.com')
        self.assertTrue(member.first_name, 'bla')
        self.assertTrue(member.groups.get().pk, self.staff.groups.get().pk)

    def test_groups_not_required(self):
        data = {
            'email': 'bla@example.com',
            'first_name': 'bla',
            'last_name': 'Example',
            'is_active': True,
            'username': 'bla@example.com',
            'password': 'bla',
            'primary_language': 'en',
            'user_type': 'person',
            'date_joined': timezone.now(),
        }
        form = MemberCreationForm(current_user=self.staff, data=data)
        form.save()

        member = Member.objects.get(email='bla@example.com')
        self.assertTrue(member.first_name, 'bla')
        self.assertTrue(len(member.groups.all()), 0)

    def test_user_not_part_of_group(self):
        group, _ = Group.objects.get_or_create(name='New group')
        data = {
            'email': 'bla@example.com',
            'first_name': 'bla',
            'last_name': 'Example',
            'is_active': True,
            'username': 'bla@example.com',
            'password': 'bla',
            'primary_language': 'en',
            'user_type': 'person',
            'date_joined': timezone.now(),
            'groups': [group.pk]
        }
        form = MemberCreationForm(current_user=self.staff, data=data)
        self.assertTrue('groups' in form.errors)


class MemberAdminFieldsTest(BluebottleTestCase):
    def setUp(self):
        super(MemberAdminFieldsTest, self).setUp()
        self.request = RequestFactory().get('/')
        self.request.user = MockUser()

        self.member = BlueBottleUserFactory.create()
        self.member_admin = MemberAdmin(Member, AdminSite())

    def test_readonly_fields(self):
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        expected_fields = set((
            'date_joined', 'last_login', 'updated', 'deleted', 'login_as_link',
            'reset_password', 'resend_welcome_link',
            'initiatives', 'events', 'assignments', 'funding',
            'is_superuser'
        ))

        self.assertEqual(expected_fields, set(fields))

    def test_readonly_fields_create(self):
        fields = self.member_admin.get_readonly_fields(self.request)
        expected_fields = set((
            'date_joined', 'last_login', 'updated', 'deleted', 'login_as_link',
            'reset_password', 'resend_welcome_link',
            'initiatives', 'events', 'assignments', 'funding',
            'is_superuser'
        ))

        self.assertEqual(expected_fields, set(fields))

    def test_email_equal_more_groups(self):
        group = Group.objects.create(name='test')
        self.member.groups.add(group)
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        self.assertTrue('email' not in fields)

    def test_email_superuser(self):
        self.member.is_superuser = True
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        self.assertTrue('email' in fields)

    def test_email_superuser_as_superuser(self):
        self.request.user.is_superuser = True
        self.member.is_superuser = True
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        self.assertTrue('email' not in fields)

    def test_email_readonly_more_groups(self):
        group = Group.objects.create(name='test')
        self.request.user.groups = Group.objects.none()
        self.member.groups.add(group)
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        self.assertTrue('email' in fields)

    def test_super_user(self):
        self.request.user.is_superuser = True
        fields = self.member_admin.get_readonly_fields(self.request, self.member)
        self.assertTrue('is_superuser' not in fields)


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
        self.member_admin = MemberAdmin(Member, AdminSite())

    def test_member_export(self):
        member = BlueBottleUserFactory.create(username='malle-eppie')
        CustomMemberFieldSettings.objects.create(name='Extra Info')
        field = CustomMemberFieldSettings.objects.create(name='How are you')
        CustomMemberField.objects.create(member=member, value='Fine', field=field)

        ParticipantFactory.create(time_spent=5, user=member, status='succeeded')
        ParticipantFactory.create(time_spent=12, user=member, status='succeeded')
        ApplicantFactory.create_batch(3, time_spent=10, user=member, status='succeeded')
        DonorFactory.create_batch(7, amount=Money(5, 'EUR'), user=member, status='succeeded')

        export_action = self.member_admin.actions[0]
        response = export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.decode('utf-8').split("\r\n")
        headers = data[0].split(",")
        user_data = []
        for row in data:
            if row.startswith('malle-eppie'):
                user_data = row.split(',')

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers, [
            'username', 'email', 'remote_id', 'first_name', 'last name',
            'date joined', 'is initiator', 'is supporter', 'is volunteer',
            'amount donated', 'time spent', 'subscribed to matching projects', 'Extra Info', 'How are you'])
        self.assertEqual(user_data[0], 'malle-eppie')
        self.assertEqual(user_data[7], 'True')
        self.assertEqual(user_data[8], 'True')
        self.assertEqual(user_data[9], u'35.00 €')
        self.assertEqual(user_data[10], '47.0')
        self.assertEqual(user_data[13], 'Fine')

    def test_member_unicode_export(self):
        member = BlueBottleUserFactory.create(username='stimpy')
        friend = CustomMemberFieldSettings.objects.create(name='Best friend')
        CustomMemberField.objects.create(member=member, value=u'Ren Höek', field=friend)

        export_action = self.member_admin.actions[0]
        response = export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.decode('utf-8').split("\r\n")
        headers = data[0].split(",")
        data = data[1].split(",")

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers[0], 'username')
        self.assertEqual(headers[12], 'Best friend')
        self.assertEqual(data[0], 'stimpy')
        self.assertEqual(data[12], u'Ren Höek')


@override_settings(SEND_WELCOME_MAIL=True)
class AccountMailAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(AccountMailAdminTest, self).setUp()
        self.add_member_url = reverse('admin:members_member_add')
        self.client.force_login(self.superuser)

        Language.objects.get_or_create(
            code='bg',
            language_name='Bulgarian',
            native_name='Български'
        )

        # Create custom account activation email
        self.message = MessageTemplate.objects.create(
            message='bluebottle.members.messages.AccountActivationMessage'
        )
        self.message.set_current_language('en')
        self.message.subject = 'You have been assimilated to {site_name}'
        self.message.body_html = 'You are no longer {first_name}.<br/><h1>We are borg</h1>'
        self.message.body_txt = 'You are no longer {first_name}.\nWe are borg'
        self.message.save()

    def test_create_user(self):
        mail.outbox = []
        BlueBottleUserFactory.create(
            first_name='Bob',
            email='bob@bob.com',
            primary_language='en'
        )
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.com'])
        self.assertEqual(welcome_email.subject, 'You have been assimilated to Test')
        self.assertTrue('You are no longer Bob.' in welcome_email.body)
        self.assertTrue('We are borg' in welcome_email.body)

    def test_resend_welcome(self):
        user = BlueBottleUserFactory.create(
            first_name='Bob',
            email='bob@bob.com',
            primary_language='en'
        )

        welkcome_email_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': user.id})
        self.client.get(welkcome_email_url)
        welcome_email = mail.outbox[1]
        self.assertEqual(welcome_email.subject, 'You have been assimilated to Test')
        self.assertEqual(welcome_email.to, ['bob@bob.com'])
        self.assertTrue('We are borg' in welcome_email.body)

    def test_create_user_no_translations_set(self):
        self.message.delete()
        MessageTemplate.objects.create(
            message='bluebottle.members.messages.AccountActivationMessage'
        )
        # Don't set any translations
        mail.outbox = []
        BlueBottleUserFactory.create(
            first_name='Bob',
            email='bob@bob.bg',
            primary_language='bg'
        )
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.bg'])
        # NL translations not set so we should receive default translation
        self.assertEqual(welcome_email.subject, 'Welcome to Test!')

    def test_create_user_language_not_set(self):
        mail.outbox = []
        BlueBottleUserFactory.create(
            first_name='Bob',
            email='bob@bob.bg',
            primary_language='bg'
        )
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.bg'])
        # BG translations not set so we should receive default language translation
        self.assertEqual(welcome_email.subject, u'You have been assimilated to Test')
        self.assertTrue(u'You are no longer Bob.' in welcome_email.body)
        self.assertTrue(u'We are borg' in welcome_email.body)

        # Now set BG translations
        self.message.set_current_language('bg')
        self.message.subject = u'Асимилирани сте към {site_name}'
        self.message.body_html = u'Ти вече не си {first_name}.<br/><h1>Ние сме Борг</h1>'
        self.message.body_txt = u'Ти вече не си {first_name}.\nНие сме Борг'
        self.message.save()
        mail.outbox = []

        BlueBottleUserFactory.create(
            first_name=u'Бубка',
            email='bubka@bob.bg',
            primary_language='bg'
        )
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bubka@bob.bg'])
        self.assertEqual(welcome_email.subject, u'Асимилирани сте към Test')
        self.assertTrue(u'Ти вече не си Бубка.' in welcome_email.body)
        self.assertTrue(u'Ние сме Борг' in welcome_email.body)
