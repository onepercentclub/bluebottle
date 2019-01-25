import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto import Random
import mock
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import RequestFactory

from bluebottle.members.models import Member
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.booking import TokenAuthentication

from bluebottle.token_auth.models import CheckedToken
from bluebottle.token_auth.tests.factories import CheckedTokenFactory


TOKEN_AUTH_SETTINGS = {
    'backend': 'token_auth.auth.booking.TokenAuthentication',
    'sso_url': 'https://example.org',
    'token_expiration': 600,
    'hmac_key': 'bbbbbbbbbbbbbbbb',
    'aes_key': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
}


class TestBookingTokenAuthentication(BluebottleTestCase):
    """
    Tests the Token Authentication backend.
    """
    def setUp(self):
        super(TestBookingTokenAuthentication, self).setUp()

        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            self.request = RequestFactory().get('/api/sso/redirect')

            # To keep things easy, let's just change the valid token to put some Xs
            # on it at the beginning of each of those lines.
            self.token = 'XbaTf5AVWkpkiACH6nNZZUVzZR0rye7rbiqrm3Qrgph5Sn3EwsFERytBwoj' \
                'XaqSdISPvvc7aefusFmHDXAJbwLvCJ3N73x4whT7XPiJz7kfrFKYal6WlD8' \
                'Xu5JZgVTmV5hdywGQkPMFT1Z7m4z1ga6Oud2KoQNhrf5cKzQ5CSdTojZmZ0' \
                'XT24jBuwm5YUqFbvwTBxg=='
            self.corrupt_token = self.token

            self.auth_backend = TokenAuthentication(self.request, token=self.token)

            self.checked_token = CheckedTokenFactory.create()
            self.data = 'time=2013-12-23 17:51:15|username=johndoe|name=John Doe' \
                        '|email=john.doe@example.com'

            # Get the new security keys to use it around in the tests.
            self.hmac_key = self.auth_backend.settings['hmac_key']
            self.aes_key = self.auth_backend.settings['aes_key']

    def _encode_message(self, message):
        """
        Helper method for unit tests which returns an encoded version of the
        message passed as an argument.

        It returns a tuple containing a string formed by two elements:

        1. A string formed by the initialization vector and the AES-128
        encrypted message.
        2. The HMAC-SHA1 hash of that string.
        """
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(
            AES.block_size - len(s) % AES.block_size)
        init_vector = Random.new().read(AES.block_size)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, init_vector)
        padded_message = pad(message)
        aes_message = init_vector + cipher.encrypt(padded_message)
        hmac_digest = hmac.new(self.hmac_key, aes_message, hashlib.sha1)

        return aes_message, hmac_digest

    def test_sso_url(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            self.assertEqual(self.auth_backend.sso_url(), TOKEN_AUTH_SETTINGS['sso_url'])

    def test_sso_url_custom_target(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            self.assertEqual(
                self.auth_backend.sso_url(target_url='/test/'),
                TOKEN_AUTH_SETTINGS['sso_url'] + '?url=%2Ftest%2F'
            )

    def test_sso_url_custom_target_unicode(self):
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            self.assertEqual(
                self.auth_backend.sso_url(target_url=u'/test/\u2026/bla'),
                TOKEN_AUTH_SETTINGS['sso_url'] + '?url=%2Ftest%2F%E2%80%A6%2Fbla'
            )

    def test_check_hmac_signature_ok(self):
        """
        Tests that the method to check up HMAC signature of the token message
        returns True when it is a valid signature.
        """
        message = base64.urlsafe_b64decode(self.checked_token.token)
        self.assertTrue(self.auth_backend.check_hmac_signature(message))

    def test_check_hmac_signature_wrong(self):
        """
        Tests the method to check up HMAC signature when the token is corrupted
        and the signatures is not valid.
        """
        message = base64.b64decode(self.corrupt_token)

        self.assertFalse(self.auth_backend.check_hmac_signature(message))

    def test_decrypts_message(self):
        """
        Tests the method to decrypt the AES encoded message.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            aes_message, hmac_digest = self._encode_message(self.data)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())
            auth_backend = TokenAuthentication(self.request, token=token)
            message = auth_backend.decrypt_message()

            self.assertEqual(
                message, {'timestamp': '2013-12-23 17:51:15',
                          'first_name': 'John',
                          'last_name': 'Doe',
                          'email': 'john.doe@example.com',
                          'username': 'john.doe@example.com',
                          'remote_id': 'john.doe@example.com'
                          })

    def test_get_login_data(self):
        """
        Tests the method to split the login message data into a 4-field tuple.
        """
        login_data = self.auth_backend.get_login_data(self.data)

        self.assertTupleEqual(
            login_data,
            (
                '2013-12-23 17:51:15',
                'johndoe',
                'John Doe',
                'john.doe@example.com'
            ))

    def test_check_timestamp_valid_token(self):
        """
        Tests the method to check the login message timestamp when a good
        token is received.
        """
        login_time = (datetime.now() - timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S')
        self.auth_backend.check_timestamp({'timestamp': login_time})

    def test_check_timestamp_timedout_token(self):
        """
        Tests the method to check the login message timestamp when a wrong
        timestamp is given.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            login_time = (datetime.now() - timedelta(
                days=self.auth_backend.settings['token_expiration'] + 1
            )).strftime('%Y-%m-%d %H:%M:%S')

            self.assertRaises(
                TokenAuthenticationError,
                self.auth_backend.check_timestamp,
                {'timestamp': login_time})

    def test_authenticate_fail_no_token(self):
        """
        Tests that ``authenticate`` method raises an exception when no token
        is provided.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            auth_backend = TokenAuthentication(self.request)
            self.assertRaisesMessage(
                TokenAuthenticationError,
                'No token provided',
                auth_backend.authenticate)

    def test_authenticate_fail_token_used(self):
        """
        Tests that ``authenticate`` method raises an exception when a used
        token is provided.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            auth_backend = TokenAuthentication(self.request, token=self.checked_token.token)

            self.assertRaisesMessage(
                TokenAuthenticationError,
                'Token was already used and is not valid',
                auth_backend.authenticate)

    def test_authenticate_fail_corrupted_token(self):
        """
        Tests that ``authenticate`` method raises an exception when a corrupt
        token is received (HMAC-SHA1 checking).
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            auth_backend = TokenAuthentication(self.request, token=self.corrupt_token)
            self.assertRaisesMessage(
                TokenAuthenticationError,
                'HMAC authentication failed',
                auth_backend.authenticate)

    def test_authenticate_fail_invalid_login_data(self):
        """
        Tests that ``authenticate`` method raises an exception when a valid
        token was received but it didn't contained valid authentication data,
        so the message contained in the token was not as expected.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            message = 'xxxx=2013-12-18 11:51:15|xxxxxxxx=johndoe|xxxx=John Doe|' \
                      'xxxxx=john.doe@example.com'
            aes_message, hmac_digest = self._encode_message(message)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())
            auth_backend = TokenAuthentication(self.request, token=token)

            self.assertRaisesMessage(
                TokenAuthenticationError,
                'Message does not contain valid login data',
                auth_backend.authenticate)

    def test_authenticate_fail_token_expired(self):
        """
        Tests that ``authenticate`` method raises an exception when the token
        expired.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            # Set up a token with an old date (year 2012).
            message = 'time=2012-12-18 11:51:15|username=johndoe|name=John Doe|' \
                      'email=john.doe@example.com'
            aes_message, hmac_digest = self._encode_message(message)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())

            auth_backend = TokenAuthentication(self.request, token=token)

            self.assertRaisesMessage(
                TokenAuthenticationError,
                'Authentication token expired',
                auth_backend.authenticate)

    def test_authenticate_successful_login(self):
        """
        Tests ``authenticate`` method when it performs a successful login.
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = 'time={0}|username=johndoe|name=John Doe|' \
                      'email=john.doe@example.com'.format(timestamp)
            aes_message, hmac_digest = self._encode_message(message)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())

            auth_backend = TokenAuthentication(self.request, token=token)
            user, created = auth_backend.authenticate()

            # Check created user data.
            self.assertEqual(user.first_name, 'John')
            self.assertEqual(user.is_active, True)

            # Check `CheckedToken` related object.
            checked_token = CheckedToken.objects.latest('pk')
            self.assertEqual(checked_token.token, token)
            self.assertEqual(checked_token.user.username, user.username)

    @mock.patch.object(get_user_model(), 'get_login_token', create=True, return_value='tralala')
    def test_login_view(self, get_jwt_token):
        """
        Test the login view for booking
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = 'time={0}|username=johndoe|name=John Doe|' \
                      'email=john.doe@example.com'.format(timestamp)
            aes_message, hmac_digest = self._encode_message(message)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())

            login_url = reverse('token-login', kwargs={'token': token})
            response = self.client.get(login_url)
            self.assertEqual(response.status_code, 302)
            user = Member.objects.get(email='john.doe@example.com')
            self.assertEqual(
                response['Location'],
                "/login-with/{}/tralala".format(user.pk)
            )

    @mock.patch.object(get_user_model(), 'get_login_token', create=True, return_value='tralala')
    def test_link_view(self, get_jwt_token):
        """
        Test the link view for booking
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = 'time={0}|username=johndoe|name=John Doe|' \
                      'email=john.doe@example.com'.format(timestamp)
            aes_message, hmac_digest = self._encode_message(message)
            token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())

            login_url = reverse('token-login-link', kwargs={'token': token, 'link': '/projects/my-project'})
            response = self.client.get(login_url)
            self.assertEqual(response.status_code, 302)

            user = Member.objects.get(email='john.doe@example.com')
            self.assertEqual(
                response['Location'],
                "/login-with/{}/tralala?next=%2Fprojects%2Fmy-project".format(user.pk)
            )

    def test_redirect_view(self):
        """
        Test the redirect view for booking
        """
        with self.settings(TOKEN_AUTH=TOKEN_AUTH_SETTINGS):
            redirect_url = reverse('token-redirect')
            response = self.client.get(redirect_url, {'url': '/projects/my-project'})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response['Location'],
                "https://example.org?url=%2Fprojects%2Fmy-project"
            )
