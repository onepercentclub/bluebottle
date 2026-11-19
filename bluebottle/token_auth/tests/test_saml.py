import os
import urllib.parse
import xml.etree.ElementTree as ET

from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.files.base import ContentFile
from django.test import TestCase, RequestFactory
from future import standard_library
from mock import patch, MagicMock
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from bluebottle.clients import properties
from bluebottle.members.models import MemberPlatformSettings, SAMLSegmentMapping
from bluebottle.members.tests.factories import SAMLAuthenticationFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.models import SAMLLog
from bluebottle.utils import translation

standard_library.install_aliases()

response_mock = MagicMock()

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SAML_REQUEST_ID = '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'


def read_response(name='valid_response.xml.base64'):
    with open(os.path.join(DATA_DIR, name)) as response_file:
        return response_file.read()


class TestSAMLTokenAuthentication(TestCase):
    """
    Tests the Token Authentication backend.
    """

    def setUp(self):
        self.session_middleware = SessionMiddleware(response_mock)
        self.method = self.create_method()

    def create_method(self, **kwargs):
        with open(os.path.join(DATA_DIR, 'idp_metadata.xml'), 'rb') as metadata_file:
            idp_metadata = ContentFile(metadata_file.read(), name='metadata.xml')

        attributes = dict(
            entity_id='https://pitbulk.no-ip.org/newonelogin/demo1/metadata.php',
            metadata_file=idp_metadata,
            remote_id_attribute='nameId',
            email_attribute='mail',
            first_name_attribute='cn',
            last_name_attribute='sn',
            work_location_attribute=None,
        )
        attributes.update(kwargs)
        SAMLAuthenticationFactory._meta.model.objects.filter(entity_id=attributes['entity_id']).delete()
        return SAMLAuthenticationFactory.create(**attributes)

    def _request(self, method, target, session=None, *args, **kwargs):
        request = getattr(RequestFactory(), method)(target, *args, **kwargs)

        middleware = SessionMiddleware(response_mock)
        middleware.process_request(request)
        if session:
            request.session.update(session)

        request.session.save()

        return request

    def _auth_request(self, response=None, session_id=SAML_REQUEST_ID, **data):
        return self._request(
            'post',
            '/sso/auth',
            session={'saml_request_id': session_id},
            HTTP_HOST='www.stuff.com',
            data=dict(SAMLResponse=read_response() if response is None else response, **data)
        )

    def _sso_url_base(self, sso_url):
        return urllib.parse.urlunparse((
            sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None
        ))

    def test_sso_url(self):
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')

        auth_backend = SAMLAuthentication(request, self.method)

        sso_url = urllib.parse.urlparse(auth_backend.sso_url())
        query = urllib.parse.parse_qs(sso_url.query)
        self.assertEqual(self._sso_url_base(sso_url), self.method.single_signon_url)

        self.assertTrue('SAMLRequest' in query)
        self.assertEqual(query['RelayState'][0], 'http://www.stuff.com/sso/redirect')
        self.assertEqual(
            request.session['saml_request_id'],
            auth_backend.auth.get_last_request_id()
        )

    def test_sso_url_custom_target(self):
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, self.method)

        sso_url = urllib.parse.urlparse(auth_backend.sso_url(target_url='/test'))
        query = urllib.parse.parse_qs(sso_url.query)
        self.assertEqual(self._sso_url_base(sso_url), self.method.single_signon_url)

        self.assertTrue('SAMLRequest' in query)
        self.assertEqual(query['RelayState'][0], '/test')

    def test_auth_succes(self):
        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        user, created = auth_backend.authenticate()

        self.assertTrue(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.first_name, 'Sixto3')
        self.assertEqual(user.last_name, 'Martin2')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
        self.assertTrue(len(SAMLLog.objects.all()), 1)

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_session_reuse(self, error):
        method = self.create_method(strict=True)
        auth_backend = SAMLAuthentication(self._auth_request(session_id='123'), method)
        self.assertRaises(
            TokenAuthenticationError,
            auth_backend.authenticate
        )
        error.assert_called()
        self.assertTrue(len(SAMLLog.objects.all()), 1)

    def _assert_rejected(self, response):
        auth_backend = SAMLAuthentication(self._auth_request(response), self.method)
        self.assertRaises(TokenAuthenticationError, auth_backend.authenticate)

    def test_auth_bad_base64_padding(self):
        self._assert_rejected('PHNhbWxwOlJlc3BvbnNlPg')

    def test_auth_base64_length_one_mod_four(self):
        self._assert_rejected('YWJjZGU')

    def test_auth_non_base64_characters(self):
        self._assert_rejected("' OR 1=1--")

    def test_auth_non_ascii_body(self):
        self._assert_rejected('éèê')

    def test_auth_empty_response(self):
        self._assert_rejected('')

    def test_auth_not_xml(self):
        self._assert_rejected(
            OneLogin_Saml2_Utils.b64encode('this is not xml at all')
        )

    def test_auth_dtd_entity(self):
        self._assert_rejected(
            OneLogin_Saml2_Utils.b64encode(
                '<?xml version="1.0"?>'
                '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://evil.example.com/x">]>'
                '<samlp:Response>&xxe;</samlp:Response>'
            )
        )

    def test_auth_xml_but_not_a_saml_response(self):
        self._assert_rejected(
            OneLogin_Saml2_Utils.b64encode('<hello>world</hello>')
        )

    def test_auth_malformed_responses_do_not_mail_admins(self):
        for response in ('PHNhbWxwOlJlc3BvbnNlPg', "' OR 1=1--", ''):
            self._assert_rejected(response)

        self.assertEqual(len(mail.outbox), 0)

    def test_auth_success_missing_field(self):
        method = self.create_method(work_location_attribute='missing')
        auth_backend = SAMLAuthentication(self._auth_request(), method)

        user, created = auth_backend.authenticate()

        self.assertTrue(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_with_existing_without_email(self):
        # Create user with empty email
        BlueBottleUserFactory.create(
            remote_id='blahblah',
            email='',
            username='blah'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        user, created = auth_backend.authenticate()

        self.assertTrue(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_existing_different_remote_id(self):
        BlueBottleUserFactory.create(
            remote_id='1234',
            email='smartin@yaco.es',
            username='blah'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        user, created = auth_backend.authenticate()

        self.assertFalse(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_existing_without_remote_id(self):
        BlueBottleUserFactory.create(
            remote_id=None,
            email='smartin@yaco.es',
            username='blah'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        user, created = auth_backend.authenticate()

        self.assertFalse(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_existing_without_remote_id_different_case(self):
        BlueBottleUserFactory.create(
            remote_id=None,
            email='SMartin@yaco.es',
            username='blah'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        user, created = auth_backend.authenticate()

        self.assertFalse(created)

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_success(self):
        # Create user with remote_id with caps
        BlueBottleUserFactory.create(
            remote_id='492882615ACF31C8096B627245D76AE53036C090',
            email='smartin@yaco.es',
            username='smartin'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        # Login should stil work.
        user, created = auth_backend.authenticate()
        self.assertFalse(created)
        self.assertEqual(user.username, 'smartin')
        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_inactive_success(self):
        # Create user with remote_id with caps
        BlueBottleUserFactory.create(
            remote_id='492882615ACF31C8096B627245D76AE53036C090',
            email='smartin@yaco.es',
            username='smartin',
            is_active=False
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        # Login should stil work.
        user, created = auth_backend.authenticate()
        self.assertFalse(created)
        self.assertEqual(user.username, 'smartin')
        self.assertTrue(user.is_active, 'smartin')

        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_with_office(self):
        method = self.create_method(work_location_attribute='cn')
        LocationFactory.create(slug='Sixto3', name='Sixto Office')

        # Create user with remote_id with caps
        BlueBottleUserFactory.create(
            remote_id='492882615ACF31C8096B627245D76AE53036C090',
            email='smartin@yaco.es',
            username='smartin'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), method)

        # Login should stil work.
        user, created = auth_backend.authenticate()
        self.assertFalse(created)
        self.assertEqual(user.username, 'smartin')
        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
        self.assertEqual(user.location.name, 'Sixto Office')

    def test_auth_existing_with_segment(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()

        segment_type = SegmentTypeFactory.create(slug='function', name='Function')
        SAMLSegmentMapping.objects.create(
            authentication_method=self.method,
            source_attribute='eduPersonAffiliation',
            segment_type=segment_type,
        )

        # Create user with remote_id with caps
        BlueBottleUserFactory.create(
            remote_id='492882615ACF31C8096B627245D76AE53036C090',
            email='smartin@yaco.es',
            username='smartin'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)

        # Login should still work.
        user, created = auth_backend.authenticate()
        self.assertFalse(created)
        self.assertEqual(user.username, 'smartin')
        self.assertEqual(user.email, 'smartin@yaco.es')
        self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
        self.assertEqual(user.segments.first().name, 'user')

    def test_auth_existing_with_segment_slug(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()

        segment_type = SegmentTypeFactory.create(slug='function', name='Function')
        segment = SegmentFactory.create(segment_type=segment_type, slug='user', name='Some other')
        SAMLSegmentMapping.objects.create(
            authentication_method=self.method,
            source_attribute='eduPersonAffiliation',
            segment_type=segment_type,
        )

        BlueBottleUserFactory.create(
            remote_id='492882615ACF31C8096B627245D76AE53036C090',
            email='smartin@yaco.es',
            username='smartin'
        )

        auth_backend = SAMLAuthentication(self._auth_request(), self.method)
        user, created = auth_backend.authenticate()
        self.assertFalse(created)
        self.assertEqual(list(user.segments.all()), [segment])

    @patch('bluebottle.token_auth.auth.base.logger.error')
    def test_auth_non_existing_no_provision(self, error):
        method = self.create_method(provision=False)
        auth_backend = SAMLAuthentication(self._auth_request(), method)

        self.assertRaises(
            TokenAuthenticationError,
            auth_backend.authenticate
        )
        error.assert_called_with(
            'Login error: User not found, and provisioning is disabled'
        )

    def test_auth_custom_target(self):
        auth_backend = SAMLAuthentication(self._auth_request(RelayState='/test'), self.method)

        self.assertEqual(auth_backend.target_url, '/test')

    def test_auth_absolute_custom_target(self):
        auth_backend = SAMLAuthentication(
            self._auth_request(RelayState='https://example.com/test'), self.method
        )

        self.assertEqual(auth_backend.target_url, '/test')

    def test_auth_admin_target(self):
        auth_backend = SAMLAuthentication(self._auth_request(RelayState='/en/admin'), self.method)

        self.assertEqual(auth_backend.target_url, '/en/admin')

    def _assert_target_rejected(self, relay_state):
        request = RequestFactory().post(
            '/sso/auth',
            HTTP_HOST='www.stuff.com',
            data={'SAMLResponse': read_response(), 'RelayState': relay_state}
        )
        auth_backend = SAMLAuthentication(request, self.method)

        self.assertIsNone(auth_backend.target_url)

    def test_auth_custom_target_non_http(self):
        self._assert_target_rejected('javascript://alert("test")')

    def test_auth_custom_target_non_http_start_with_space(self):
        self._assert_target_rejected(' javascript://alert("test")')

    def test_auth_custom_target_other_domain(self):
        self._assert_target_rejected('https://bla.com')

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_invalid(self, error):
        auth_backend = SAMLAuthentication(
            self._auth_request(read_response('invalid_response.xml.base64')), self.method
        )

        self.assertRaises(
            TokenAuthenticationError,
            auth_backend.authenticate
        )
        self.assertTrue(
            (
                'Saml login error: [\'invalid_response\'], reason: '
                'Signature validation failed. SAML Response rejected, '
                'assertions: '
            ) in error.call_args[0][0]
        )

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_no_response(self, error):
        request = self._request(
            'post',
            '/sso/auth',
            session={'saml_request_id': SAML_REQUEST_ID},
            HTTP_HOST='www.stuff.com',
        )
        auth_backend = SAMLAuthentication(request, self.method)

        self.assertRaises(
            TokenAuthenticationError,
            auth_backend.authenticate
        )

        error.assert_called_with((
            'Saml login error: SAML Response not found, '
            'Only supported HTTP_POST Binding'
        ))

    def _saml_request_tree(self):
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, self.method)

        sso_url = urllib.parse.urlparse(auth_backend.sso_url())
        query = urllib.parse.parse_qs(sso_url.query)
        self.assertEqual(self._sso_url_base(sso_url), self.method.single_signon_url)

        saml_xml = OneLogin_Saml2_Utils.decode_base64_and_inflate(query['SAMLRequest'][0])
        return ET.fromstring(saml_xml)

    def test_saml_request_omits_name_id_policy(self):
        # Make sure NameIDPolicy doesn't show up in SAMLReuqest
        pre = {'samlp': "urn:oasis:names:tc:SAML:2.0:protocol"}
        nip = self._saml_request_tree().findall('samlp:NameIDPolicy', pre)

        self.assertEqual(len(nip), 0)

    def test_saml_request_omits_authentication_context(self):
        # Make sure RequestedAuthnContext doesn't show up in SAMLReuqest
        pre = {'samlp': "urn:oasis:names:tc:SAML:2.0:protocol"}
        rac = self._saml_request_tree().findall('samlp:RequestedAuthnContext', pre)
        self.assertEqual(len(rac), 0)

    def test_parse_user(self):
        method = self.create_method(work_location_attribute='location')
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, method)

        result = auth_backend.parse_user({
            'mail': ['test@example.com'],
            'nameId': ['1234325'],
            'cn': ['Test'],
            'sn': ['User'],
            'location': ['Amsterdam'],
        })
        self.assertEqual(result, {
            'remote_id': '1234325',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'work_location': 'Amsterdam',
        })

    def _segment_backend(self, segment_type):
        SAMLSegmentMapping.objects.create(
            authentication_method=self.method,
            source_attribute='segment',
            segment_type=segment_type,
        )
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        return SAMLAuthentication(request, self.method)

    def _set_segments(self, auth_backend, user, values):
        auth_backend.attributes = {'segment': values}
        auth_backend.set_segments(user, {})

    def test_parse_segments(self):
        segment_type = SegmentTypeFactory.create(slug='segment')
        SegmentFactory.create(
            segment_type=segment_type,
            name='Marketing',
            alternate_names=['MarkCom', 'Propaganda', 'Online Marketing']
        )
        SegmentFactory.create(
            segment_type=segment_type,
            name='Sales'
        )

        language = properties.LANGUAGE_CODE

        user = BlueBottleUserFactory.create()
        auth_backend = self._segment_backend(segment_type)

        self._set_segments(auth_backend, user, ['Online Marketing', 'Marketing'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Marketing']
        )
        self._set_segments(auth_backend, user, ['Sales', 'Marketing'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Sales']
        )
        self._set_segments(auth_backend, user, ['markeTING'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Marketing']
        )

    def test_parse_segments_translated_names(self):
        """Test that segment matching works with translated segment names."""
        from bluebottle.utils.models import Language

        Language.objects.get_or_create(code='en', defaults={'default': True})
        Language.objects.get_or_create(code='nl', defaults={'default': False})

        segment_type = SegmentTypeFactory.create(slug='segment')

        marketing_segment = SegmentFactory.create(
            segment_type=segment_type,
            name='Marketing',
            alternate_names=['MarkCom', 'Propaganda', 'Online Marketing']
        )
        marketing_segment.set_current_language('nl')
        marketing_segment.name = 'Prodaganda'
        marketing_segment.save()

        sales_segment = SegmentFactory.create(
            segment_type=segment_type,
            name='Sales',
            alternate_names=['Sales Team']
        )
        sales_segment.set_current_language('nl')
        sales_segment.name = 'Verkoop'
        sales_segment.save()
        sales_segment.alternate_names.append('Verkoop')
        sales_segment.save()

        language = properties.LANGUAGE_CODE

        user = BlueBottleUserFactory.create()
        auth_backend = self._segment_backend(segment_type)

        # Test matching with Dutch translated name in alternate_names
        self._set_segments(auth_backend, user, ['Verkoop'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Sales']
        )
        # Verify it matches the correct segment by checking Dutch translation
        with translation.override('nl'):
            self.assertEqual(
                list(user.segments.translated('nl').values_list('translations__name', flat=True)),
                ['Verkoop']
            )

        # Test case-insensitive matching with translated name
        self._set_segments(auth_backend, user, ['VERKOOP'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Sales']
        )

        # Test matching with English name still works
        self._set_segments(auth_backend, user, ['Marketing'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Marketing']
        )

    def test_parse_segments_translated_names_slug_match(self):
        """Test that segment matching works with translated names via slug matching."""
        from bluebottle.utils.models import Language

        Language.objects.get_or_create(code='en', defaults={'default': True})
        Language.objects.get_or_create(code='nl', defaults={'default': False})

        segment_type = SegmentTypeFactory.create(slug='segment')

        # Create a segment with English name "Support" and Dutch name "Ondersteuning"
        # The slug will be based on the English name
        support_segment = SegmentFactory.create(
            segment_type=segment_type,
            name='Support',
            alternate_names=[]  # No alternate names, so it will match via slug
        )
        # Set Dutch translation
        support_segment.set_current_language('nl')
        support_segment.name = 'Ondersteuning'
        support_segment.save()

        language = properties.LANGUAGE_CODE

        user = BlueBottleUserFactory.create()
        auth_backend = self._segment_backend(segment_type)

        # Test matching via slug (the slug is based on English name "support")
        self._set_segments(auth_backend, user, ['support'])
        self.assertEqual(
            list(user.segments.translated(language).values_list('translations__name', flat=True)),
            ['Support']
        )
        # Verify Dutch translation is correct
        with translation.override('nl'):
            self.assertEqual(
                list(user.segments.translated('nl').values_list('translations__name', flat=True)),
                ['Ondersteuning']
            )

    def test_parse_user_missing(self):
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, self.method)

        result = auth_backend.parse_user({
            'nameId': ['1234325']
        })
        self.assertEqual(
            result['remote_id'], '1234325'
        )
        self.assertTrue('email' not in result)
        self.assertTrue('first_name' not in result)

    def test_parse_user_partial(self):
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, self.method)

        result = auth_backend.parse_user({
            'nameId': ['1234325'],
            'cn': ['Test']
        })
        self.assertEqual(
            result['remote_id'], '1234325'
        )
        self.assertEqual(
            result['first_name'], 'Test'
        )

        self.assertTrue('email' not in result)

    def test_empty_claims(self):
        method = self.create_method(work_location_attribute='location')
        request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
        auth_backend = SAMLAuthentication(request, method)

        result = auth_backend.parse_user({
            'nameId': ['1234325'],
            'location': ['amsterdam']
        })
        self.assertEqual(
            result['work_location'], 'amsterdam'
        )

        result = auth_backend.parse_user({
            'nameId': ['4573457'],
            'location': []
        })
        self.assertTrue('work_location' not in result)
