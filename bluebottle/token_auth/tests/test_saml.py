import urlparse
import os
from mock import patch

from django.test import TestCase, RequestFactory

from onelogin.saml2.utils import OneLogin_Saml2_Utils
import xml.etree.ElementTree as ET

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.tests.saml_settings import TOKEN_AUTH2_SETTINGS

from .saml_settings import TOKEN_AUTH_SETTINGS


class TestSAMLTokenAuthentication(TestCase):
    """
    Tests the Token Authentication backend.
    """
    def test_sso_url(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = RequestFactory().get('/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request)

            sso_url = urlparse.urlparse(auth_backend.sso_url())
            query = urlparse.parse_qs(sso_url.query)
            self.assertEqual(
                urlparse.urlunparse((
                    sso_url.scheme, sso_url.netloc, sso_url.path, None, None, None)
                ),
                TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url']
            )

            self.assertTrue('SAMLRequest' in query)
            self.assertEqual(query['RelayState'][0], 'http://www.stuff.com/sso/redirect')

    def test_sso_url_custom_target(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = RequestFactory().get('/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request)

            sso_url = urlparse.urlparse(auth_backend.sso_url(target_url='/test'))
            query = urlparse.parse_qs(sso_url.query)
            self.assertEqual(
                urlparse.urlunparse((
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

            request = RequestFactory().post('/sso/auth', HTTP_HOST='www.stuff.com', data={'SAMLResponse': response})
            auth_backend = SAMLAuthentication(request)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_with_existing_without_email(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Create user with empty email
            BlueBottleUserFactory.create(remote_id='blahblah',
                               email='',
                               username='blah')

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post('/sso/auth', HTTP_HOST='www.stuff.com', data={'SAMLResponse': response})
            auth_backend = SAMLAuthentication(request)

            user, created = auth_backend.authenticate()

            self.assertTrue(created)

            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_existing_succes(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Create user with remote_id with caps
            BlueBottleUserFactory.create(remote_id='492882615ACF31C8096B627245D76AE53036C090',
                               email='smartin@yaco.es',
                               username='smartin')

            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post('/sso/auth', HTTP_HOST='www.stuff.com', data={'SAMLResponse': response})
            auth_backend = SAMLAuthentication(request)

            # Login should stil work.
            user, created = auth_backend.authenticate()
            self.assertFalse(created)
            self.assertEqual(user.username, 'smartin')
            self.assertEqual(user.email, 'smartin@yaco.es')
            self.assertEqual(user.remote_id, '492882615acf31c8096b627245d76ae53036c090')

    def test_auth_custom_target(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/valid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post(
                '/sso/auth',
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response, 'RelayState': '/test'}
            )
            auth_backend = SAMLAuthentication(request)

            self.assertEqual(auth_backend.target_url, '/test')

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_invalid(self, error):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            filename = os.path.join(
                os.path.dirname(__file__), 'data/invalid_response.xml.base64'
            )
            with open(filename) as response_file:
                response = response_file.read()

            request = RequestFactory().post(
                '/sso/auth',
                HTTP_HOST='www.stuff.com',
                data={'SAMLResponse': response}
            )
            auth_backend = SAMLAuthentication(request)

            self.assertRaises(
                TokenAuthenticationError,
                auth_backend.authenticate
            )
            error.assert_called_with((
                'Saml login error: [\'invalid_response\'], reason: '
                'Signature validation failed. SAML Response rejected'
            ))

    @patch('bluebottle.token_auth.auth.saml.logger.error')
    def test_auth_no_response(self, error):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            request = RequestFactory().post('/sso/auth', HTTP_HOST='www.stuff.com')
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
            request = RequestFactory().get('/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request)

            sso_url = urlparse.urlparse(auth_backend.sso_url())
            query = urlparse.parse_qs(sso_url.query)
            self.assertEqual(
                urlparse.urlunparse((
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
            request = RequestFactory().get('/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request)

            sso_url = urlparse.urlparse(auth_backend.sso_url())
            query = urlparse.parse_qs(sso_url.query)
            self.assertEqual(
                urlparse.urlunparse((
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
            request = RequestFactory().get('/sso/redirect', HTTP_HOST='www.stuff.com')
            auth_backend = SAMLAuthentication(request)

            sso_url = urlparse.urlparse(auth_backend.sso_url())
            query = urlparse.parse_qs(sso_url.query)
            self.assertEqual(
                urlparse.urlunparse((
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
