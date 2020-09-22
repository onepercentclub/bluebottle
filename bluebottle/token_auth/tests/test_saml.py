from future import standard_library
standard_library.install_aliases()
import urllib.parse
import os
from mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory

from onelogin.saml2.utils import OneLogin_Saml2_Utils
import xml.etree.ElementTree as ET

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.tests.saml_settings import TOKEN_AUTH2_SETTINGS

from .saml_settings import TOKEN_AUTH_SETTINGS
from ...test.factory_models.geo import LocationFactory


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

            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

            # BB-17150
            # Make sure the request cannot be repeated
            # self.assertRaises(
            #     TokenAuthenticationError,
            #     auth_backend.authenticate
            # )

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
            auth_backend = SAMLAuthentication(request)
            self.assertRaises(
                TokenAuthenticationError,
                auth_backend.authenticate
            )
            error.assert_called()

    def test_auth_succes_missing_field(self):
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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_succes(self):
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
            auth_backend = SAMLAuthentication(request)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
            auth_backend = SAMLAuthentication(request)

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
