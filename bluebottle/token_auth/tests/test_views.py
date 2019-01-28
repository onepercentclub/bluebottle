import urllib

from django.contrib.sessions.middleware import SessionMiddleware
from django.test.utils import override_settings
from django.test import RequestFactory
from django.test.testcases import TestCase

from mock import patch

from bluebottle.token_auth.auth import booking, base
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.views import get_auth, TokenRedirectView, TokenLoginView


DUMMY_AUTH = {'backend': 'token_auth.tests.test_views.DummyAuthentication'}


class DummyUser(object):
    pk = 1

    class _meta:
        class pk:
            @staticmethod
            def value_to_string(obj):
                return 1

    def get_login_token(self):
        return 'test-token'

    def save(self, *args, **kwargs):
        pass


class DummyAuthentication(base.BaseTokenAuthentication):
    def authenticate(self):
        if getattr(self.request, 'fails', False):
            raise TokenAuthenticationError('test message')

        return DummyUser(), True

    @property
    def target_url(self):
        return self.args['link']


class ConfigureAuthenticationClassTestCase(TestCase):
    """
    Tests the configuration of the authentication backend
    """
    @override_settings(TOKEN_AUTH={'backend': 'token_auth.auth.booking.TokenAuthentication'})
    def test_booking_class(self):
        request = RequestFactory().get('/api/sso/redirect')
        auth = get_auth(request, token='test-token')
        self.assertTrue(isinstance(auth, booking.TokenAuthentication))
        self.assertEqual(auth.args['token'], 'test-token')

    @override_settings(TOKEN_AUTH={'backend': 'non-existing-module.non-existing-class'})
    def test_incorrect_class(self):
        request = RequestFactory().get('/api/sso/redirect')
        self.assertRaises(
            ImportError,
            get_auth,
            request
        )


@override_settings(TOKEN_AUTH=DUMMY_AUTH)
class RedirectViewTestCase(TestCase):
    def setUp(self):
        self.view = TokenRedirectView()
        self.factory = RequestFactory()

    @patch('bluebottle.token_auth.tests.test_views.DummyAuthentication.sso_url',
           return_value='http://example.com/sso')
    def test_get(self, sso_url):
        response = self.view.get(self.factory.get('/api/sso/redirect'))
        expected_url = 'http://example.com/sso'

        sso_url.assert_called_once_with(target_url=None)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    @patch('bluebottle.token_auth.tests.test_views.DummyAuthentication.sso_url',
           return_value='http://example.com/sso')
    def test_get_custom_target(self, sso_url):

        response = self.view.get(
            self.factory.get('/api/sso/redirect?' + urllib.urlencode({'url': '/test/'}))
        )
        sso_url.assert_called_once_with(target_url='/test/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://example.com/sso')


@override_settings(TOKEN_AUTH=DUMMY_AUTH)
class LoginViewTestCase(TestCase):
    def setUp(self):
        self.view = TokenLoginView()
        self.factory = RequestFactory()

    def test_get(self):
        response = self.view.get(self.factory.get('/api/sso/authenticate'))
        user = DummyUser()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'], '/login-with/{}/{}'.format(user.pk, user.get_login_token())
        )

    def test_get_link(self):
        response = self.view.get(self.factory.get('/api/sso/authenticate'), link='/test')
        user = DummyUser()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            '/login-with/{}/{}?next=%2Ftest'.format(user.pk, user.get_login_token())
        )

    def test_admin(self):
        admin_link = '/en/admin/projects'

        request = self.factory.get('/api/sso/authenticate')
        SessionMiddleware().process_request(request)
        request.session.save()

        response = self.view.get(request, link=admin_link)
        user = DummyUser()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            admin_link
        )
        self.assertEqual(request.session['_auth_user_id'], 1)

    def test_get_authentication_failed(self):
        request = self.factory.get('/api/sso/authenticate')
        request.fails = True

        response = self.view.get(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            "/token/error?message='test%20message'"
        )
