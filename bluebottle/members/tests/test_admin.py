# coding=utf-8
import os
from builtins import object
from datetime import timedelta

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core import mail
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from djmoney.money import Money

from bluebottle.collect.tests.factories import CollectContributorFactory
from bluebottle.funding.tests.factories import DonorFactory
from bluebottle.funding_pledge.models import PledgePaymentProvider
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.admin import MemberAdmin, MemberCreationForm
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.notifications.models import MessageTemplate
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateParticipantFactory, PeriodParticipantFactory, ParticipationFactory
)
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
        self.assertEqual(response.status_code, 302)
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['bob@bob.com'])
        self.assertTrue('Set password' in welcome_email.body)
        self.assertTrue('test@example.com' in welcome_email.body,
                        'Tenant contact email should be present.')

    def test_password_mail(self):
        user = BlueBottleUserFactory.create()
        member_url = reverse('admin:members_member_change', args=(user.id,))
        response = self.client.get(member_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Send reset password mail')

        # Assert password reset link sends the right email
        reset_url = reverse('admin:auth_user_password_reset_mail', kwargs={'pk': user.id})

        confirm_response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Are you sure' in confirm_response.content)

        response = self.client.post(reset_url, {'confirm': True})
        self.assertEqual(response.status_code, 302)
        reset_mail = mail.outbox[0]
        self.assertEqual(reset_mail.to, [user.email])
        self.assertTrue('Seems you\'ve requested a password reset for' in reset_mail.body)

    def test_password_mail_anonymous(self):
        user = BlueBottleUserFactory.create()
        self.client.logout()
        reset_url = reverse('admin:auth_user_password_reset_mail', kwargs={'pk': user.id})
        response = self.client.post(reset_url, {'confirm': True})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_welcome(self):
        user = BlueBottleUserFactory.create(welcome_email_is_sent=True)
        member_url = reverse('admin:members_member_change', args=(user.id,))
        response = self.client.get(member_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resend welcome email')

        welcome_email_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': user.id})

        confirm_response = self.client.get(welcome_email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Are you sure' in confirm_response.content)

        response = self.client.post(welcome_email_url, {'confirm': True})
        self.assertEqual(response.status_code, 302)
        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, [user.email])
        self.assertTrue(
            'Welcome {}'.format(user.first_name) in welcome_email.body
        )

    def test_resend_welcome_anonymous(self):
        user = BlueBottleUserFactory.create()
        self.client.logout()

        welcome_email_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': user.id})
        response = self.client.post(welcome_email_url, {'confirm': True})
        self.assertEqual(response.status_code, 403)


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
        expected_fields = {
            'date_joined', 'last_login', 'updated', 'deleted', 'login_as_link', 'reset_password',
            'resend_welcome_link', 'initiatives', 'period_activities', 'date_activities', 'funding',
            'deeds', 'collect', 'is_superuser', 'kyc', 'hours_planned', 'hours_spent', 'all_contributions'
        }

        self.assertEqual(expected_fields, set(fields))

    def test_readonly_fields_create(self):
        fields = self.member_admin.get_readonly_fields(self.request)
        expected_fields = {
            'date_joined', 'last_login', 'updated', 'deleted', 'login_as_link', 'reset_password',
            'resend_welcome_link', 'initiatives', 'date_activities', 'period_activities', 'funding',
            'deeds', 'collect', 'is_superuser', 'kyc', 'hours_planned', 'hours_spent', 'all_contributions'
        }

        self.assertEqual(expected_fields, set(fields))
        self.member_admin = MemberAdmin(Member, AdminSite())

    def test_can_pledge_field(self):
        fieldsets = self.member_admin.get_fieldsets(self.request, self.member)
        self.assertFalse('can_pledge' in fieldsets[2][1]['fields'])
        PledgePaymentProvider.objects.create()
        fieldsets = self.member_admin.get_fieldsets(self.request, self.member)
        self.assertTrue('can_pledge' in fieldsets[2][1]['fields'])

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


class MemberPlatformSettingsAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def test_require_location(self):
        LocationFactory.create_batch(3)
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:members_memberplatformsettings_change'))
        form = page.forms[0]
        form['require_office'].checked = True

        form.submit()
        settings_platform = MemberPlatformSettings.load()
        self.assertTrue(settings_platform.require_office)

    def test_require_profile_fields(self):
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:members_memberplatformsettings_change'))
        form = page.forms[0]
        form['require_address'].checked = True
        form['require_birthdate'].checked = True
        form['require_phone_number'].checked = True

        form.submit()
        settings_platform = MemberPlatformSettings.load()
        self.assertTrue(settings_platform.require_phone_number)
        self.assertTrue(settings_platform.require_address)
        self.assertTrue(settings_platform.require_birthdate)

    def test_create_initiatives(self):
        LocationFactory.create_batch(3)
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:members_memberplatformsettings_change'))
        form = page.forms[0]
        form['create_initiatives'].checked = True

        form.submit()
        settings_platform = MemberPlatformSettings.load()
        self.assertTrue(settings_platform.create_initiatives)

    def test_fiscal_year(self):
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:members_memberplatformsettings_change'))
        form = page.forms[0]
        form['fiscal_month_offset'] = '4'

        form.submit()
        settings_platform = MemberPlatformSettings.load()
        self.assertEqual(settings_platform.fiscal_month_offset, 4)


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
        self.export_action = self.member_admin.get_actions(self.request)['export_as_csv'][0]

    def test_member_export(self):
        member = BlueBottleUserFactory.create()

        ParticipationFactory.create(
            value=timedelta(hours=5),
            contributor=DateParticipantFactory(user=member, status='accepted'),
            status='succeeded'
        )
        ParticipationFactory.create(
            value=timedelta(hours=12),
            contributor=PeriodParticipantFactory(user=member, status='accepted'),
            status='succeeded'
        )
        ParticipationFactory.create_batch(
            3,
            value=timedelta(hours=10),
            contributor=DateParticipantFactory(user=member, status='accepted'),
            status='succeeded'
        )
        DonorFactory.create_batch(7, amount=Money(5, 'EUR'), user=member, status='succeeded')

        response = self.export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.decode('utf-8').split("\r\n")
        headers = data[0].split(";")
        user_data = []
        for row in data:
            if row.startswith(member.email):
                user_data = row.split(';')

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers, [
            'email', 'phone number', 'remote id', 'first name', 'last name',
            'date joined', 'is initiator', 'is supporter', 'is volunteer',
            'amount donated', 'time spent', 'subscribed to matching projects'])
        self.assertEqual(user_data[0], member.email)
        self.assertEqual(user_data[7], 'True')
        self.assertEqual(user_data[8], 'True')

        self.assertEqual(user_data[9], u'35.00 €')
        self.assertEqual(user_data[10], '47.0')

    def test_member_unicode_export(self):
        member = BlueBottleUserFactory.create(
            first_name='Ren',
            last_name='Höek'
        )

        response = self.export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.decode('utf-8').split("\r\n")
        headers = data[0].split(";")
        data = data[1].split(";")

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers[0], 'email')
        self.assertEqual(data[0], member.email)
        self.assertEqual(data[4], u'Höek')

    def test_member_segments_export(self):
        member = BlueBottleUserFactory.create(email='malle@eppie.nl')
        food = SegmentTypeFactory.create(name='Food')
        bb = SegmentFactory.create(segment_type=food, name='Bitterballen')
        drinks = SegmentTypeFactory.create(name='Drinks')
        br = SegmentFactory.create(segment_type=drinks, name='Bier')
        member.segments.add(bb)
        member.segments.add(br)
        member.save()
        response = self.export_action(self.member_admin, self.request, self.member_admin.get_queryset(self.request))

        data = response.content.decode('utf-8').split("\r\n")
        headers = data[0].split(";")
        user_data = []
        for row in data:
            if row.startswith('malle@eppie.nl'):
                user_data = row.split(';')

        # Test basic info and extra field are in the csv export
        self.assertEqual(headers, [
            'email', 'phone number', 'remote id', 'first name', 'last name',
            'date joined', 'is initiator', 'is supporter', 'is volunteer',
            'amount donated', 'time spent', 'subscribed to matching projects', 'Drinks', 'Food'])
        self.assertEqual(user_data[12], 'Bier')
        self.assertEqual(user_data[13], 'Bitterballen')


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
        welcome_email = mail.outbox[0]
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


class MemberEngagementAdminTestCase(BluebottleAdminTestCase):

    def test_engagement_shows_donations(self):
        user = BlueBottleUserFactory.create()
        DonorFactory.create_batch(10, user=user, status='succeeded', amount=Money(35, 'EUR'))
        url = reverse('admin:members_member_change', args=(user.id,))
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('Funding donations:' in response.text)
        self.assertTrue(
            '<a href="/en/admin/funding/donor/?user_id={}">10</a> donations'.format(user.id)
            in response.text
        )

    def test_engagement_shows_initiative_owner(self):
        user = BlueBottleUserFactory.create()
        InitiativeFactory.create_batch(5, owner=user)
        url = reverse('admin:members_member_change', args=(user.id,))
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('Initiatives:' in response.text)
        self.assertTrue(
            '<a href="/en/admin/initiatives/initiative/?owner_id={}">5</a>'.format(user.id)
            in response.text
        )

    def test_engagement_shows_collect(self):
        user = BlueBottleUserFactory.create()
        CollectContributorFactory.create(user=user)
        url = reverse('admin:members_member_change', args=(user.id,))
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('Collect contributor:' in response.text)
        self.assertTrue(
            '<a href="/en/admin/collect/collectcontributor/'
            '?user_id={}&amp;status=succeeded">1</a> succeeded'.format(user.id)
            in response.text
        )


class MemberNotificationsAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(MemberNotificationsAdminTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()

        self.member_admin_url = reverse(
            'admin:members_member_change',
            args=(self.user.id,)
        )

    def test_initiative_admin(self):
        self.app.set_user(self.staff_member)

        # Normal user should not have submitted_initiative_notifications checkbox
        page = self.app.get(self.member_admin_url)
        self.assertFalse('id_submitted_initiative_notifications' in page.text)
        form = page.forms[0]
        form.set('is_staff', True)
        form.submit()

        # Made user into a staff member
        # Should have submitted_initiative_notifications checkbox now
        page = self.app.get(self.member_admin_url)
        self.assertTrue('id_submitted_initiative_notifications' in page.text)
        form = page.forms[0]
        form.set('submitted_initiative_notifications', True)
        form.submit()

        self.user.refresh_from_db()
        self.assertTrue(self.user.submitted_initiative_notifications)

        # Demote user into normal member
        # Should unset submitted_initiative_notifications boolean
        page = self.app.get(self.member_admin_url)
        form = page.forms[0]
        form.set('is_staff', False)
        form.submit()

        self.user.refresh_from_db()
        self.assertFalse(self.user.submitted_initiative_notifications)
