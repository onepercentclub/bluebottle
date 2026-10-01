import logging

from django.test import RequestFactory, TestCase

from bluebottle.token_auth.views import TokenRedirectView


class TokenRedirectTargetUrlTestCase(TestCase):
    """BB-30159: ?url= was passed straight to build_absolute_uri().

    Two problems, both exercised by a scanner against the Mars tenant:

    * a look-alike separator (U+FF0F instead of '/') makes urlsplit raise
      `ValueError: netloc ... contains invalid characters under NFKC
      normalization` inside build_absolute_uri, which escaped the view as an
      unhandled 500;
    * `//evil.example.com` does *not* raise -- it parses cleanly and
      build_absolute_uri returns the attacker's URL, which was then handed to
      the IdP as the AuthnRequest RelayState.
    """

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
