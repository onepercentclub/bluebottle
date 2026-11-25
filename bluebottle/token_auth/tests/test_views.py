import logging
import os
import uuid
from xml.etree import ElementTree
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from bluebottle.members.models import (
    AuthenticationLog, Member, MemberPlatformSettings, SAMLGroupMapping, SAMLSegmentMapping
)
from bluebottle.members.tests.factories import SAMLAuthenticationFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.token_auth.views import TokenRedirectView


class TokenRedirectTargetUrlTestCase(TestCase):
    def setUp(self):
        self.view = TokenRedirectView()

    def enable_logging(self):
        # bluebottle/settings/testing.py disables logging globally, which would
        # make the two assertions below pass without proving anything.
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)

    def target_url(self, url=None):
        query = {'url': url} if url is not None else {}
        return self.view.target_url(RequestFactory().get('/token/redirect/', query))

    def test_relative_path_is_kept(self):
        self.assertEqual(
            self.target_url('/en/initiatives'),
            'http://testserver/en/initiatives',
        )

    def test_absolute_url_on_the_same_host_is_kept(self):
        self.assertEqual(
            self.target_url('http://testserver/en/activities'),
            'http://testserver/en/activities',
        )

    def test_absolute_url_on_https(self):
        self.assertEqual(
            self.target_url('https://testserver/en/activities'),
            'https://testserver/en/activities',
        )

    def test_missing_url_falls_back_to_the_tenant_root(self):
        self.assertEqual(self.target_url(), 'http://testserver/')

    def test_empty_url_falls_back_to_the_tenant_root(self):
        self.assertEqual(self.target_url(''), 'http://testserver/')

    def test_off_host_url_does_not_redirect_off_tenant(self):
        """This one never raised -- it silently passed the value through."""
        for url in ('//evil.example.com', 'https://evil.example.com/pwn'):
            self.assertEqual(
                self.target_url(url),
                'http://testserver/',
                'accepted off-host url {}'.format(url),
            )

    def test_nfkc_payload_does_not_raise(self):
        """The exact value from the report: U+FF0F fullwidth solidus."""
        self.assertEqual(
            self.target_url('//ptst.io／acts.mars.com'),
            'http://testserver/',
        )

    def test_malformed_url_does_not_raise(self):
        for url in ('http://[', '//['):
            self.assertEqual(
                self.target_url(url),
                'http://testserver/',
                'raised or accepted malformed url {}'.format(url),
            )

    def test_rejected_url_is_logged_as_a_warning(self):
        """Scanner traffic should not page devops at ERROR level."""
        self.enable_logging()

        with self.assertLogs('bluebottle.token_auth.views', level='WARNING') as logs:
            self.target_url('//evil.example.com')

        self.assertEqual(len(logs.records), 1)
        self.assertEqual(logs.records[0].levelname, 'WARNING')

    def test_accepted_url_is_not_logged(self):
        self.enable_logging()

        with self.assertNoLogs('bluebottle.token_auth.views', level='WARNING'):
            self.target_url('/en/initiatives')


class TokenRedirectViewTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.method = SAMLAuthenticationFactory.create()
        self.url = reverse('token-auth:saml-redirect', args=(self.method.pk, ))

    def get_redirect(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        location = urlparse(response['Location'])
        return location, parse_qs(location.query)

    def test_redirects_to_idp_of_method(self):
        location, query = self.get_redirect(self.url)

        self.assertEqual(
            '{}://{}{}'.format(location.scheme, location.netloc, location.path),
            self.method.single_signon_url
        )
        self.assertIn('SAMLRequest', query)

    def test_uses_settings_of_requested_method(self):
        other = SAMLAuthenticationFactory.create()
        location, _query = self.get_redirect(
            reverse('token-auth:saml-redirect', args=(other.pk, ))
        )

        self.assertEqual(
            '{}://{}{}'.format(location.scheme, location.netloc, location.path),
            other.single_signon_url
        )
        self.assertNotEqual(other.single_signon_url, self.method.single_signon_url)

    def test_relay_state_is_target_url(self):
        _location, query = self.get_redirect(self.url + '?url=/en/initiatives')

        self.assertEqual(query['RelayState'], ['http://test.localhost/en/initiatives'])

    def test_relay_state_defaults_to_root(self):
        _location, query = self.get_redirect(self.url + '?url=//evil.example.com')

        self.assertEqual(query['RelayState'], ['http://test.localhost/'])

    def test_stores_request_id_in_session(self):
        self.get_redirect(self.url)

        self.assertTrue(self.client.session['saml_request_id'])

    def test_unknown_method(self):
        response = self.client.get(
            reverse('token-auth:saml-redirect', args=(uuid.uuid4(), ))
        )
        self.assertEqual(response.status_code, 404)

    def test_disabled_method(self):
        self.method.enabled = False
        self.method.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_without_idp_metadata(self):
        self.method.metadata_file = None
        self.method.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_restricted_ips_excluding_current_ip(self):
        self.method.restricted_ips = ['198.51.100.1']
        self.method.save()

        response = self.client.get(self.url, REMOTE_ADDR='203.0.113.10')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('saml_request_id', self.client.session)

    def test_restricted_ips_including_current_ip(self):
        self.method.restricted_ips = ['198.51.100.1', '203.0.113.10']
        self.method.save()

        response = self.client.get(self.url, REMOTE_ADDR='203.0.113.10')
        self.assertEqual(response.status_code, 302)


class MetadataViewTestCase(BluebottleTestCase):
    namespaces = {'md': 'urn:oasis:names:tc:SAML:2.0:metadata'}

    def setUp(self):
        super().setUp()
        self.method = SAMLAuthenticationFactory.create()
        self.url = reverse('token-auth:saml-metadata', args=(self.method.pk, ))

    def get_metadata(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/xml')
        return ElementTree.fromstring(response.content)

    def test_metadata(self):
        root = self.get_metadata(self.url)

        self.assertEqual(root.tag, '{urn:oasis:names:tc:SAML:2.0:metadata}EntityDescriptor')
        self.assertEqual(root.get('entityID'), self.method.entity_id)

    def test_assertion_consumer_service(self):
        root = self.get_metadata(self.url)

        service = root.find('md:SPSSODescriptor/md:AssertionConsumerService', self.namespaces)
        self.assertEqual(
            service.get('Location'),
            'http://test.localhost{}'.format(reverse('token-auth:saml-login'))
        )
        self.assertEqual(service.get('Binding'), 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST')

    def test_single_logout_service(self):
        root = self.get_metadata(self.url)

        service = root.find('md:SPSSODescriptor/md:SingleLogoutService', self.namespaces)
        self.assertEqual(
            service.get('Location'),
            'http://test.localhost{}'.format(reverse('token-auth:saml-logout'))
        )

    def test_name_id_format(self):
        root = self.get_metadata(self.url)

        name_id_format = root.find('md:SPSSODescriptor/md:NameIDFormat', self.namespaces)
        self.assertEqual(name_id_format.text, self.method.name_id_format)

    def test_uses_requested_method(self):
        other = SAMLAuthenticationFactory.create()
        root = self.get_metadata(reverse('token-auth:saml-metadata', args=(other.pk, )))

        self.assertEqual(root.get('entityID'), other.entity_id)
        self.assertNotEqual(other.entity_id, self.method.entity_id)

    def test_without_idp_metadata(self):
        self.method.metadata_file = None
        self.method.save()

        root = self.get_metadata(self.url)
        self.assertEqual(root.get('entityID'), self.method.entity_id)

    def test_unknown_method(self):
        response = self.client.get(
            reverse('token-auth:saml-metadata', args=(uuid.uuid4(), ))
        )
        self.assertEqual(response.status_code, 404)


class SAMLLoginViewTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()

        data_dir = os.path.join(os.path.dirname(__file__), 'data')

        # The entityID in idp_metadata.xml must match the <saml:Issuer> in valid_response.xml.base64
        with open(os.path.join(data_dir, 'idp_metadata.xml'), 'rb') as metadata_file:
            idp_metadata = ContentFile(metadata_file.read(), name='metadata.xml')

        self.method = SAMLAuthenticationFactory.create(
            entity_id='https://pitbulk.no-ip.org/newonelogin/demo1/metadata.php',
            metadata_file=idp_metadata,
            remote_id_attribute='uid',
            email_attribute='mail',
            first_name_attribute='cn',
            last_name_attribute='sn',
        )
        self.url = reverse('token-auth:saml-login')

        filename = os.path.join(os.path.dirname(__file__), 'data/valid_response.xml.base64')
        with open(filename) as response_file:
            self.saml_response = response_file.read()

    def login(self, **extra):
        return self.client.post(
            self.url,
            urlencode({'SAMLResponse': self.saml_response, 'RelayState': '/en/admin'}),
            format=None,
            content_type='application/x-www-form-urlencoded',
            **extra
        )

    def assert_logged_in_as(self, user):
        self.assertEqual(Member.objects.filter(email__iexact='smartin@yaco.es').count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.remote_id, 'smartin')
        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.first_name, 'Sixto3')
        self.assertEqual(user.last_name, 'Martin2')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_valid_response_logs_user_in(self):
        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/admin')

        user = Member.objects.get(email='smartin@yaco.es')
        self.assertEqual(user.remote_id, 'smartin')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        log = AuthenticationLog.objects.get()
        self.assertEqual(log.user, user)
        self.assertEqual(log.method.pk, self.method.pk)

    def test_frontend_login_creates_authentication_log(self):
        response = self.client.post(
            self.url,
            urlencode({'SAMLResponse': self.saml_response, 'RelayState': '/en/initiatives'}),
            format=None,
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, 200)

        log = AuthenticationLog.objects.get()
        self.assertEqual(log.user, Member.objects.get(email='smartin@yaco.es'))
        self.assertEqual(log.method.pk, self.method.pk)

    def test_existing_user_by_remote_id_logs_in(self):
        user = BlueBottleUserFactory.create(
            remote_id='smartin',
            email='someone-else@example.com',
            first_name='Old',
            last_name='Name',
        )

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/admin')
        self.assert_logged_in_as(user)

    def test_existing_user_by_remote_id_different_case_logs_in(self):
        user = BlueBottleUserFactory.create(remote_id='SMartin', email='someone-else@example.com')

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assert_logged_in_as(user)

    def test_existing_user_by_email_logs_in(self):
        user = BlueBottleUserFactory.create(remote_id=None, email='SMartin@yaco.es')

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assert_logged_in_as(user)

    def test_no_provision_existing_user_logs_in(self):
        self.method.provision = False
        self.method.save()
        user = BlueBottleUserFactory.create(remote_id='smartin', email='someone-else@example.com')

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/admin')
        self.assert_logged_in_as(user)

    def test_no_provision_new_user_cannot_log_in(self):
        self.method.provision = False
        self.method.save()

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/token/error'))
        self.assertIn('Account%20not%20found', response['Location'])
        self.assertFalse(Member.objects.filter(email__iexact='smartin@yaco.es').exists())
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(AuthenticationLog.objects.exists())

    def test_disabled_method_new_user_cannot_log_in(self):
        self.method.enabled = False
        self.method.save()

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/token/error'))
        self.assertFalse(Member.objects.filter(email__iexact='smartin@yaco.es').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_disabled_method_existing_user_cannot_log_in(self):
        self.method.enabled = False
        self.method.save()
        user = BlueBottleUserFactory.create(
            remote_id='smartin', email='someone-else@example.com', first_name='Old'
        )

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/token/error'))
        self.assertNotIn('_auth_user_id', self.client.session)
        user.refresh_from_db()
        self.assertEqual(user.email, 'someone-else@example.com')
        self.assertEqual(user.first_name, 'Old')

    def test_restricted_ips_empty_allows_login(self):
        self.assertEqual(self.method.restricted_ips, [])

        response = self.login(REMOTE_ADDR='203.0.113.10')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/admin')
        self.assert_logged_in_as(Member.objects.get(email='smartin@yaco.es'))

    def test_restricted_ips_excluding_current_ip_blocks_login(self):
        self.method.restricted_ips = ['198.51.100.1', '198.51.100.2']
        self.method.save()

        response = self.login(REMOTE_ADDR='203.0.113.10')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Member.objects.filter(email__iexact='smartin@yaco.es').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_restricted_ips_including_current_ip_allows_login(self):
        self.method.restricted_ips = ['198.51.100.1']
        self.method.save()

        response = self.login(REMOTE_ADDR='203.0.113.10')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)

        self.method.restricted_ips = ['198.51.100.1', '203.0.113.10']
        self.method.save()

        response = self.login(REMOTE_ADDR='203.0.113.10')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/en/admin')
        self.assert_logged_in_as(Member.objects.get(email='smartin@yaco.es'))

    def test_restricted_ips_uses_forwarded_for_header(self):
        self.method.restricted_ips = ['203.0.113.10']
        self.method.save()

        response = self.login(
            REMOTE_ADDR='10.0.0.1',
            HTTP_X_FORWARDED_FOR='192.0.2.5, 203.0.113.10'
        )

        self.assertEqual(response.status_code, 302)
        self.assert_logged_in_as(Member.objects.get(email='smartin@yaco.es'))

    def add_segment_mapping(self, segment_type, source_attribute='eduPersonAffiliation'):
        return SAMLSegmentMapping.objects.create(
            authentication_method=self.method,
            segment_type=segment_type,
            source_attribute=source_attribute,
        )

    def test_segment_mapping_sets_segment(self):
        role = SegmentTypeFactory.create(name='Role')
        user_segment = SegmentFactory.create(name='User', segment_type=role, alternate_names=[])
        SegmentFactory.create(name='Reviewer', segment_type=role, alternate_names=[])
        self.add_segment_mapping(role)

        response = self.login()

        self.assertEqual(response.status_code, 302)
        user = Member.objects.get(email='smartin@yaco.es')
        # Only the first value of a multi-valued attribute is used
        self.assertEqual(list(user.segments.all()), [user_segment])

    def test_segment_mapping_matches_alternate_name(self):
        role = SegmentTypeFactory.create(name='Role')
        segment = SegmentFactory.create(name='Employee', segment_type=role, alternate_names=['user'])
        self.add_segment_mapping(role)

        self.login()

        user = Member.objects.get(email='smartin@yaco.es')
        self.assertEqual(list(user.segments.all()), [segment])

    def test_segment_mapping_replaces_unverified_segment(self):
        role = SegmentTypeFactory.create(name='Role')
        user_segment = SegmentFactory.create(name='User', segment_type=role, alternate_names=[])
        other_segment = SegmentFactory.create(name='Reviewer', segment_type=role, alternate_names=[])
        self.add_segment_mapping(role)

        user = BlueBottleUserFactory.create(remote_id='smartin', email='smartin@yaco.es')
        user.segments.add(other_segment, through_defaults={'verified': False})

        self.login()

        self.assertEqual(list(user.segments.all()), [user_segment])

    def test_segment_mapping_unknown_segment(self):
        role = SegmentTypeFactory.create(name='Role')
        SegmentFactory.create(name='Reviewer', segment_type=role, alternate_names=[])
        self.add_segment_mapping(role)

        response = self.login()

        self.assertEqual(response.status_code, 302)
        user = Member.objects.get(email='smartin@yaco.es')
        self.assertEqual(user.segments.count(), 0)

    def test_segment_mapping_creates_segment(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()

        role = SegmentTypeFactory.create(name='Role')
        self.add_segment_mapping(role)

        self.login()

        user = Member.objects.get(email='smartin@yaco.es')
        segment = user.segments.get()
        self.assertEqual(segment.segment_type, role)
        self.assertEqual(segment.name, 'user')

    def test_segment_mapping_missing_attribute(self):
        role = SegmentTypeFactory.create(name='Role')
        SegmentFactory.create(name='User', segment_type=role, alternate_names=[])
        self.add_segment_mapping(role, source_attribute='department')

        response = self.login()

        self.assertEqual(response.status_code, 302)
        user = Member.objects.get(email='smartin@yaco.es')
        self.assertEqual(user.segments.count(), 0)

    def add_group_mapping(self, group_name, group_names=('Support',), **kwargs):
        group = Group.objects.get_or_create(name=group_name)[0]
        SAMLGroupMapping.objects.create(
            authentication_method=self.method,
            group=group,
            group_names=list(group_names),
            **kwargs
        )
        return group

    def login_with_groups(self, groups=('Support', 'Sales')):
        # The test response is signed, so we cannot add a group attribute to it.
        # Inject it into the parsed attributes instead.
        get_attributes = OneLogin_Saml2_Auth.get_attributes

        def get_attributes_with_groups(auth):
            return dict(
                get_attributes(auth),
                **{'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups': list(groups)}
            )

        with mock.patch.object(OneLogin_Saml2_Auth, 'get_attributes', get_attributes_with_groups):
            response = self.login()

        self.assertEqual(response.status_code, 302)
        return Member.objects.get(email='smartin@yaco.es')

    def test_group_mapping_adds_user_to_group(self):
        group = self.add_group_mapping('Partner', staff=False)

        user = self.login_with_groups()

        self.assertIn(group, user.groups.all())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_group_mapping_set_staff(self):
        group = self.add_group_mapping('Staff', staff=True)

        user = self.login_with_groups()

        self.assertIn(group, user.groups.all())
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_group_mapping_set_superuser(self):
        group = self.add_group_mapping('Staff', staff=True, superuser=True)

        user = self.login_with_groups()

        self.assertIn(group, user.groups.all())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_group_mapping_without_group_names_applies_to_nobody(self):
        group = self.add_group_mapping('Staff', group_names=(), staff=True, superuser=True)

        user = self.login_with_groups()

        self.assertNotIn(group, user.groups.all())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_group_mapping_matches_any_group_name(self):
        group = self.add_group_mapping('Partner', group_names=('Marketing', 'Sales'))

        user = self.login_with_groups()

        self.assertIn(group, user.groups.all())

    def test_group_mapping_no_match(self):
        group = self.add_group_mapping('Partner', group_names=('Marketing',), staff=True)

        user = self.login_with_groups()

        self.assertNotIn(group, user.groups.all())
        self.assertFalse(user.is_staff)

    def test_group_mapping_without_groups_claim(self):
        group = self.add_group_mapping('Partner')

        response = self.login()

        self.assertEqual(response.status_code, 302)
        user = Member.objects.get(email='smartin@yaco.es')
        self.assertNotIn(group, user.groups.all())
