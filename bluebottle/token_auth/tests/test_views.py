import logging
import uuid
from xml.etree import ElementTree
from urllib.parse import parse_qs, urlparse

from django.test import RequestFactory, TestCase
from django.urls import reverse

from bluebottle.members.tests.factories import SAMLAuthenticationFactory
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
