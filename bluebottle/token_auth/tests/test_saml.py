import os
import urllib.parse
import xml.etree.ElementTree as ET

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from future import standard_library
from mock import patch
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.models import SAMLLog
from bluebottle.token_auth.tests.saml_settings import TOKEN_AUTH2_SETTINGS, TOKEN_AUTH_SETTINGS

from bluebottle.clients import properties

standard_library.install_aliases()


class TestSAMLTokenAuthentication(TestCase):
    """
    Tests the Token Authentication backend.
    """

    def setUp(self):
        self.session_middleware = SessionMiddleware()

    def _request(self, method, target, session=None, *args, **kwargs):
        request = getattr(RequestFactory(), method)(target, *args, **kwargs)

        middleware = SessionMiddleware()
        middleware.process_request(request)
        if session:
            request.session.update(session)

        request.session.save()

        return request

    def test_sso_url(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')

            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            sso_url = urllib.parse.urlparse(auth_backend.sso_url())
            query = urllib.parse.parse_qs(sso_url.query)
            self.assertEqual(
                urllib.parse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )

            self.assertTrue('SAMLRequest' in query)
            self.assertEqual(query['RelayState'][0], 'http://www.stuff.com/sso/redirect')
            self.assertEqual(
                request.session['saml_request_id'],
                auth_backend.auth.get_last_request_id()
            )

    def test_sso_url_custom_target(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            sso_url = urllib.parse.urlparse(auth_backend.sso_url(target_url='/test'))
            query = urllib.parse.parse_qs(sso_url.query)
            self.assertEqual(
                urllib.parse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )

            self.assertTrue('SAMLRequest' in query)
            self.assertEqual(query['RelayState'][0], '/test')

    def test_auth_succes(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
            self.assertTrue(len(SAMLLog.objects.all()), 1)

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_session_reuse(self, error):
        settings = dict(TOKEN_AUTH_SETTINGS, strict=True)
        with self.settings(TOKEN_AUTH=settings):

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '123'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)
            self.assertRaises(
                TokenAuthenticationError,
                auth_backend.authenticate
            )
            error.assert_called()
            self.assertTrue(len(SAMLLog.objects.all()), 1)

    def test_auth_success_missing_field(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['is_staff'] = 'test'

        with self.settings(TOKEN_AUTH=settings):

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_with_existing_without_email(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Create user with empty email
            BlueBottleUserFactory.create(
                remote_id='blahblah',
                email='',
                username='blah'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_existing_without_remote_id(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            user = BlueBottleUserFactory.create(
                remote_id=None,
                email='smartin@yaco.es',
                username='blah'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            user, created = auth_backend.authenticate()

            self.assertFalse(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_existing_without_remote_id_different_case(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            user = BlueBottleUserFactory.create(
                remote_id=None,
                email='SMartin@yaco.es',
                username='blah'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            user, created = auth_backend.authenticate()

            self.assertFalse(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_success(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_inactive_success(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin',
                is_active=False
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertTrue(user.is_active, 'smartin')

            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_with_office(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['location.slug'] = 'cn'
        LocationFactory.create(slug='Sixto3', name='Sixto Office')

        with self.settings(TOKEN_AUTH=settings):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
            self.assertEqual(user.location.name, 'Sixto Office')

    def test_auth_existing_with_office_name(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['location.name'] = 'cn'
        LocationFactory.create(slug='sixt', name='Sixto3')

        with self.settings(TOKEN_AUTH=settings):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
            self.assertEqual(user.location.name, 'Sixto3')
            self.assertEqual(user.location.slug, 'sixt')

    def test_auth_existing_with_segment(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()

        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['segment.function'] = 'eduPersonAffiliation'
        SegmentTypeFactory.create(slug='function', name='Function')

        with self.settings(TOKEN_AUTH=settings):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

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

        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['segment.function'] = 'eduPersonAffiliation'
        segment_type = SegmentTypeFactory.create(slug='function', name='Function')
        SegmentFactory.create(segment_type=segment_type, slug='user', name='Some other')

        with self.settings(TOKEN_AUTH=settings):
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)
            user, created = auth_backend.authenticate()
            self.assertFalse(created)

    def test_auth_existing_with_office_and_segment(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings['assertion_mapping']['location.slug'] = 'eduPersonAffiliation'
        settings['assertion_mapping']['segment.function'] = 'eduPersonAffiliation'

        LocationFactory.create(slug='user', name='User Office')
        member_settings = MemberPlatformSettings.load()
        member_settings.create_segments = True
        member_settings.save()
        SegmentTypeFactory.create(slug='function', name='Function')

        with self.settings(TOKEN_AUTH=settings):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(
                remote_id='492882615ACF31C8096B627245D76AE53036C090',
                email='smartin@yaco.es',
                username='smartin'
            )

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')
            self.assertEqual(user.location.name, 'User Office')
            self.assertEqual(user.segments.first().name, 'user')

    @patch('bluebottle.token_auth.auth.base.logger.error')
    def test_auth_non_existing_no_provision(self, error):
        token_auth_settings = dict(provision=False, **TOKEN_AUTH_SETTINGS)
        with self.settings(TOKEN_AUTH=token_auth_settings):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            # Login should stil work.
            self.assertRaises(
                TokenAuthenticationError,
                auth_backend.authenticate
            )
            error.assert_called_with(
                'Login error: User not found, and provisioning is disabled'
            )

    def test_auth_custom_target(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response, 'RelayState': '/test'}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            self.assertEqual(auth_backend.target_url, '/test')

    def test_auth_custom_target_non_http(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post(
                '/sso/auth',
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response, 'RelayState': 'javascript://alert("test")'}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            self.assertIsNone(auth_backend.target_url)

    def test_auth_custom_target_non_http_start_with_space(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post(
                '/sso/auth',
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response, 'RelayState': ' javascript://alert("test")'}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            self.assertIsNone(auth_backend.target_url)

    def test_auth_custom_target_other_domain(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post(
                '/sso/auth',
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response, 'RelayState': 'https://bla.com'}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            self.assertIsNone(auth_backend.target_url)

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_invalid(self, error):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/invalid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

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
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = self._request(
                'post',
                '/sso/auth',
                session={'saml_request_id': '_6273d77b8cde0c333ec79d22a9fa0003b9fe2d75cb'},
                HTTP_HOST='www.stuff.com',
            )
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            self.assertRaises(
                TokenAuthenticationError,
                auth_backend.authenticate
            )

            error.assert_called_with((
                'Saml login error: SAML Response not found, '
                'Only supported HTTP_POST Binding'
            ))

    def test_saml_request_omits_name_id_policy(self):
        # Make sure NameIDPolicy doesn't show up in SAMLReuqest
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            sso_url = urllib.parse.urlparse(auth_backend.sso_url())
            query = urllib.parse.parse_qs(sso_url.query)
            self.assertEqual(
                urllib.parse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )
            saml_request = query['SAMLRequest'][0]
            saml_xml = OneLogin_Saml2_Utils.decode_base64_and_inflate(saml_request)
            pre = {'samlp': "urn:oasis:names:tc:SAML:2.0:protocol"}
            tree = ET.fromstring(saml_xml)
            nip = tree.findall('samlp:NameIDPolicy', pre)

            self.assertEqual(len(nip), 0)

    def test_saml_request_omits_authentication_context(self):
        # Make sure RequestedAuthnContext doesn't show up in SAMLReuqest
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            sso_url = urllib.parse.urlparse(auth_backend.sso_url())
            query = urllib.parse.parse_qs(sso_url.query)
            self.assertEqual(
                urllib.parse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )
            saml_request = query['SAMLRequest'][0]
            saml_xml = OneLogin_Saml2_Utils.decode_base64_and_inflate(saml_request)
            pre = {'samlp': "urn:oasis:names:tc:SAML:2.0:protocol"}
            tree = ET.fromstring(saml_xml)
            rac = tree.findall('samlp:RequestedAuthnContext', pre)
            self.assertEqual(len(rac), 0)

    def test_saml_request_sets_authentication_context(self):
        # Make sure RequestedAuthnContext has right property in SAMLReuqest
        with self.settings(TOKEN_AUTH=TOKEN_AUTH2_SETTINGS):
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            sso_url = urllib.parse.urlparse(auth_backend.sso_url())
            query = urllib.parse.parse_qs(sso_url.query)
            self.assertEqual(
                urllib.parse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )
            saml_request = query['SAMLRequest'][0]
            saml_xml = OneLogin_Saml2_Utils.decode_base64_and_inflate(saml_request)
            pre = {'samlp': "urn:oasis:names:tc:SAML:2.0:protocol"}
            tree = ET.fromstring(saml_xml)
            rac = tree.findall('samlp:RequestedAuthnContext', pre)
            self.assertEqual(len(rac), 1)
            # Comparison property should be set to minimal
            self.assertEqual(rac[0].attrib['Comparison'], "minimal")
            # RequestedAuthnContext should have 6 options / children
            self.assertEqual(len(rac[0]), 6)

    def test_parse_user(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings.update(
            assertion_mapping={
                'email': 'mail',
                'remote_id': 'nameId',
                'segment.team': ['team', 'team_name']
            }
        )

        with self.settings(TOKEN_AUTH=settings):

            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            result = auth_backend.parse_user({
                'team': ['Marketing'],
                'team_name': ['Online Marketing'],
                'mail': ['test@example.com'],
                'nameId': ['1234325']
            })
            self.assertEqual(
                result['remote_id'], '1234325'
            )
            self.assertEqual(
                result['email'], 'test@example.com'
            )
            self.assertEqual(
                result['segment.team'], ['Marketing', 'Online Marketing']
            )

    def test_parse_segments(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings.update(
            assertion_mapping={
                'email': 'mail',
                'remote_id': 'nameId',
                'segment.segment': ['segment', 'section'],
            }
        )

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

        with self.settings(TOKEN_AUTH=settings):
            user = BlueBottleUserFactory.create()
            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            auth_backend.set_segments(user, {
                'segment.segment': ['Online Marketing', 'Marketing']
            })
            self.assertEqual(
                list(user.segments.values_list('name', flat=True)),
                ['Marketing']
            )
            auth_backend.set_segments(user, {
                'segment.segment': ['Sales', 'Marketing']
            })
            self.assertEqual(
                list(user.segments.values_list('name', flat=True)),
                ['Marketing', 'Sales']
            )
            auth_backend.set_segments(user, {
                'segment.segment': ['markeTING']
            })
            self.assertEqual(
                list(user.segments.values_list('name', flat=True)),
                ['Marketing']
            )

    def test_parse_user_missing(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings.update(
            assertion_mapping={
                'email': 'mail',
                'remote_id': 'nameId',
                'segment.team': ['team', 'team_name']
            }
        )

        with self.settings(TOKEN_AUTH=settings):

            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            result = auth_backend.parse_user({
                'nameId': ['1234325']
            })
            self.assertEqual(
                result['remote_id'], '1234325'
            )
            self.assertTrue('email' not in result)
            self.assertTrue('segment.team' not in result)

    def test_parse_user_partial(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        settings.update(
            assertion_mapping={
                'email': 'mail',
                'remote_id': 'nameId',
                'segment.team': ['team', 'team_name']
            }
        )

        with self.settings(TOKEN_AUTH=settings):

            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            result = auth_backend.parse_user({
                'nameId': ['1234325'],
                'team': ['Marketing']
            })
            self.assertEqual(
                result['remote_id'], '1234325'
            )
            self.assertEqual(
                result['segment.team'], ['Marketing']
            )

            self.assertTrue('email' not in result)

    def test_empty_claims(self):
        settings = dict(**TOKEN_AUTH_SETTINGS)
        LocationFactory.create(slug='amsterdam')
        settings.update(
            assertion_mapping={
                'email': 'mail',
                'remote_id': 'nameId',
                'location.slug': 'location',
            }
        )

        with self.settings(TOKEN_AUTH=settings):

            request = self._request('get', '/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request, properties.TOKEN_AUTH)

            result = auth_backend.parse_user({
                'nameId': ['1234325'],
                'location': ['amsterdam']
            })
            self.assertEqual(
                result['location.slug'], 'amsterdam'
            )

            result = auth_backend.parse_user({
                'nameId': ['4573457'],
                'location': []
            })
            self.assertEqual(
                result['location.slug'], ''
            )
