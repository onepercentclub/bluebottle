import json
import time
from builtins import range
from calendar import timegm
from datetime import datetime, timedelta, date

import jwt
import mock
from captcha import client
from django.core import mail
from django.core.signing import TimestampSigner
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework_jwt.settings import api_settings

from bluebottle.auth.middleware import authorization_logger
from bluebottle.clients import properties
from bluebottle.members.models import MemberPlatformSettings, UserActivity, Member
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import PlaceFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class LoginTestCase(BluebottleTestCase):
    """
    Integration tests for the SignUp token api endpoint.
    """
    def setUp(self):
        self.password = 'blablabla'
        self.email = 'test@example.com'
        self.user = BlueBottleUserFactory.create(email=self.email, password=self.password)
        super(LoginTestCase, self).setUp()

    def test_login(self):
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.json()['token']
        decoded = jwt.decode(
            token, algorithms='HS256', options=dict(verify_signature=False)
        )

        self.assertEquals(list(decoded.keys()), ['username', 'exp', 'orig_iat'])
        self.assertEqual(decoded['username'], self.user.pk)

        current_user_response = self.client.get(
            reverse('user-current'), token='JWT {}'.format(token)
        )

        self.assertEqual(current_user_response.status_code, status.HTTP_200_OK)

    def test_login_formencoded(self):
        response = self.client.post(
            reverse('token-auth'),
            {'email': self.email, 'password': self.password},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_login_different_case(self):
        response = self.client.post(
            reverse('token-auth'),
            {'email': self.email.replace('test', 'Test'), 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        current_user_response = self.client.get(
            reverse('user-current'), token='JWT {}'.format(response.json()['token'])
        )

        self.assertEqual(current_user_response.status_code, status.HTTP_200_OK)

    def test_expired_token(self):
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.json()['token']

        with mock.patch('jwt.api_jwt.datetime') as mock_datetime:
            mock_datetime.utcnow = mock.Mock(
                return_value=datetime.utcnow() + timedelta(days=8)
            )

            current_user_response = self.client.get(
                reverse('user-current'), token='JWT {}'.format(token)
            )

            self.assertEqual(current_user_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_exp_in_properties(self):
        properties.JWT_EXPIRATION_DELTA = timedelta(hours=1)

        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.json()['token']

        current_user_response = self.client.get(
            reverse('user-current'), token='JWT {}'.format(token)
        )

        self.assertEqual(current_user_response.status_code, status.HTTP_200_OK)

        with mock.patch('jwt.api_jwt.datetime') as mock_datetime:
            mock_datetime.utcnow = mock.Mock(
                return_value=datetime.utcnow() + timedelta(minutes=61)
            )

            current_user_response = self.client.get(
                reverse('user-current'), token='JWT {}'.format(token)
            )

            self.assertEqual(current_user_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_renewal(self):
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.json()['token']

        current_user_response = self.client.get(
            reverse('user-current'), token='JWT {}'.format(token)
        )

        self.assertFalse('Refresh-Token' in current_user_response)

        with mock.patch('bluebottle.auth.middleware.datetime') as mock_datetime:
            mock_datetime.utcnow = mock.Mock(
                return_value=datetime.utcnow() + timedelta(minutes=31)
            )

            current_user_response = self.client.get(
                reverse('user-current'), token='JWT {}'.format(token)
            )
            self.assertTrue('Refresh-Token' in current_user_response)

            current_user_response = self.client.get(
                reverse('user-current'), token=current_user_response['Refresh-Token']
            )
            self.assertEqual(current_user_response.status_code, status.HTTP_200_OK)

    def test_login_failed(self):
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_failed_multiple(self):

        with mock.patch.object(authorization_logger, 'error') as logger:
            for i in range(0, 14):
                response = self.client.post(
                    reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
                )
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

            response = self.client.post(
                reverse('token-auth'), {'email': self.email, 'password': self.password}
            )

            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertTrue(logger.call_count < 11)

    def test_login_failed_captcha(self):
        for i in range(0, 11):
            self.client.post(
                reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
            )

        mock_response = client.RecaptchaResponse(True, extra_data={'hostname': 'testserver'})

        with mock.patch.object(client, 'submit', return_value=mock_response):
            json_api_client = JSONAPITestClient()
            captcha_response = json_api_client.post(
                reverse('captcha-verification'),
                {'data': {'type': 'captcha-tokens', 'attributes': {'token': 'test-token'}}},
            )

        self.assertEqual(captcha_response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_inactive(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(SEND_WELCOME_MAIL=True)
class SignUpTokenTestCase(BluebottleTestCase):
    """
    Integration tests for the SignUp token api endpoint.
    """
    def setUp(self):
        (self.settings, _) = MemberPlatformSettings.objects.get_or_create()

        super(SignUpTokenTestCase, self).setUp()

        self.client = JSONAPITestClient()

    def test_create(self):
        email = 'test@example.com'
        connection.tenant.name = 'Test'
        connection.tenant.save()

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        member = Member.objects.get(email=email)
        self.assertTrue('{}:'.format(member.pk) in mail.outbox[0].body)
        self.assertEqual('Activate your account for Test', mail.outbox[0].subject)
        self.assertFalse(member.is_active)

    def test_create_custom_url(self):
        email = 'test@example.com'
        connection.tenant.name = 'Test'
        connection.tenant.save()

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email, 'url': '/example'}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        member = Member.objects.get(email=email)
        self.assertTrue('{}:'.format(member.pk) in mail.outbox[0].body)
        self.assertTrue('url=/example' in mail.outbox[0].body)
        self.assertEqual('Activate your account for Test', mail.outbox[0].subject)
        self.assertFalse(member.is_active)

    def test_create_twice(self):
        email = 'test@example.com'

        self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 2)

        member = Member.objects.get(email=email)
        self.assertFalse(member.is_active)

    def test_create_twice_different_case(self):
        email = 'test@example.com'

        self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email.title()}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 2)

        member = Member.objects.get(email__iexact=email)
        self.assertFalse(member.is_active)

    def test_create_already_active(self):
        email = 'test@example.com'

        Member.objects.create(email=email, is_active=True)

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json()['errors'][0]['detail'], 'a member with this email address already exists.')
        self.assertEqual(len(mail.outbox), 1)

    def test_create_already_active_different_case(self):
        email = 'test@example.com'

        Member.objects.create(email=email, is_active=True)

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email.title()}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json()['errors'][0]['detail'], 'a member with this email address already exists.')
        self.assertEqual(len(mail.outbox), 1)

    def test_create_correct_domain(self):
        email = 'test@example.com'
        self.settings.email_domain = 'example.com'
        self.settings.save()

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        member = Member.objects.get(email=email)
        self.assertFalse(member.is_active)

    def test_create_incorrect_domain(self):
        email = 'test@secondexample.com'
        self.settings.email_domain = 'example.com'
        self.settings.save()

        response = self.client.post(
            reverse('user-signup-token'),
            {'data': {'attributes': {'email': email}, 'type': 'signup-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(
            'Only emails' in response.json()['errors'][0]['detail']
        )


@override_settings(SEND_WELCOME_MAIL=True)
class CreateUserTestCase(BluebottleTestCase):
    def setUp(self):
        (self.settings, _) = MemberPlatformSettings.objects.get_or_create()

        super(CreateUserTestCase, self).setUp()

    def test_create(self):
        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'email_confirmation': email}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        member = Member.objects.get(email=email)

        self.assertEqual(member.is_active, True)
        self.assertTrue(member.check_password(password))

    def test_create_invalid(self):
        email = 'test@example%2ecom'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'password_confirmation': password}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['email'][0],
            'Enter a valid email address.'
        )

    def test_create_twice(self):
        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'email_confirmation': email}
        )
        user_id = str(response.json()['id'])

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'email_confirmation': email}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['non_field_errors'][0]['email'],
            email
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['type'],
            'email'
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['id'],
            user_id
        )

    def test_create_twice_different_case(self):
        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'email_confirmation': email}
        )
        user_id = str(response.json()['id'])

        response = self.client.post(
            reverse('user-user-create'),
            {
                'email': email.replace('test', 'Test'),
                'password': password,
                'email_confirmation': email.replace('test', 'Test')
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['non_field_errors'][0]['email'],
            email
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['type'],
            'email'
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['id'],
            user_id
        )

    def test_failed_multiple(self):
        email = 'test@example.com'
        password = 'secret1234'
        Member.objects.create(email=email)

        for i in range(0, 11):
            response = self.client.post(
                reverse('user-user-create'),
                {'email': email, 'password': password, 'email_confirmation': email}
            )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_require_confirmation(self):
        self.settings.confirm_signup = True
        self.settings.save()

        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'email_confirmation': email}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['token'][0], 'Signup requires a confirmation token')


@override_settings(SEND_WELCOME_MAIL=True)
class ConfirmSignUpTestCase(BluebottleTestCase):
    def setUp(self):
        (self.settings, _) = MemberPlatformSettings.objects.get_or_create()

        super(ConfirmSignUpTestCase, self).setUp()
        self.email = 'test@example.com'
        self.password = 'some-password'
        self.member = Member.objects.create(email=self.email, is_active=False)
        self.token = TimestampSigner().sign(self.member.pk)

        mail.outbox = []
        self.client = JSONAPITestClient()
        self.data = {
            'data': {
                'attributes': {
                    'password': self.password,
                    'first_name': 'Tester',
                    'last_name': 'de Test',
                    'token': self.token,
                },
                'type': 'signup-token-confirmations'
            },
        }
        self.url = reverse('user-signup-token-confirm')

    def test_confirm(self):
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.member.refresh_from_db()

        self.assertEqual(self.member.is_active, True)
        self.assertTrue(self.member.check_password(self.password))
        self.assertEqual(self.member.first_name, 'Tester')
        self.assertEqual(self.member.last_name, 'de Test')

        profile_response = self.client.get(
            reverse('user-current'),
            HTTP_AUTHORIZATION='JWT {}'.format(response.json()['data']['attributes']['jwt-token'])
        )
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to Test!')

    def test_confirm_twice(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['errors'][0]['detail'],
            'The link to activate your account has already been used.'
        )

    def test_confirm_expired_token(self):
        email = 'henkie@example.com'
        password = 'henkie@example.com'

        member = Member.objects.create(email=email, is_active=False)

        current_time = time.time()

        with mock.patch('time.time', return_value=current_time - (25 * 60 * 60)):
            self.data['data']['attributes']['token'] = TimestampSigner().sign(member.pk)

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['errors'][0]['detail'],
            'The link to activate your account has expired. Please sign up again.'
        )

        member.refresh_from_db()

        self.assertEqual(member.is_active, False)
        self.assertFalse(member.check_password(password))

    def test_confirm_wrong_token(self):
        self.data['data']['attributes']['token'] = self.token + 'bla'

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['errors'][0]['detail'],
            'Something went wrong on our side. Please sign up again.'
        )

        self.member.refresh_from_db()

        self.assertEqual(self.member.is_active, False)
        self.assertFalse(self.member.check_password(self.password))


class UserDataExportTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        super(UserDataExportTest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()
        self.user_2_token = "JWT {0}".format(self.user_2.get_jwt_token())

        # User with partner organization
        self.user_export_url = reverse('user-export')

    def test_current_user(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.user_export_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)
        self.assertEqual(response.data['last_name'], self.user_1.first_name)

    def test_user_2_(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.user_export_url, token=self.user_2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], self.user_2.first_name)
        self.assertEqual(response.data['last_name'], self.user_2.first_name)

    def test_unauthenticated(self):
        response = self.client.get(self.user_export_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EmailSetTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        super(EmailSetTest, self).setUp()

        self.user = BlueBottleUserFactory.create(
            password='some-password',
            email='user@example.com'
        )
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.current_user_url = reverse('user-current')

        self.set_email_url = reverse('user-set-email')

    def test_update_email(self):
        response = self.client.put(
            self.set_email_url,
            {'password': 'some-password', 'email': 'new@example.com'},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertTrue('password' not in response.data)
        self.assertTrue('jwt_token' in response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

        old_token_response = self.client.get(
            self.current_user_url, token=self.user_token
        )
        self.assertTrue(old_token_response.status_code, status.HTTP_403_FORBIDDEN)

        new_token_response = self.client.get(
            self.current_user_url, token='JWT {}'.format(response.data['jwt_token'])
        )
        self.assertTrue(new_token_response.status_code, status.HTTP_200_OK)

    def test_update_duplicate(self):
        existing_user = BlueBottleUserFactory.create()

        response = self.client.put(
            self.set_email_url,
            {'password': 'some-password', 'email': existing_user.email},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['email'][0], "member with this email address already exists.")

    def test_update_duplicate_upper_case(self):
        existing_user = BlueBottleUserFactory.create()

        response = self.client.put(
            self.set_email_url,
            {'password': 'some-password', 'email': existing_user.email},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['email'][0], "member with this email address already exists.")

    def test_update_email_unauthenticated(self):
        response = self.client.put(
            self.set_email_url,
            {'password': 'some-password', 'email': 'new@example.com'},
        )

        self.assertEqual(response.status_code, 401)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'user@example.com')

    def test_update_email_wrong_password(self):
        response = self.client.put(
            self.set_email_url,
            {'password': 'other-password', 'email': 'new@example.com'},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 403)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'user@example.com')

    def test_update_email_wrong_token(self):
        other_user = BlueBottleUserFactory.create(
            password='some-password',
            email='other@example.com'
        )

        response = self.client.put(
            self.set_email_url,
            {'password': 'other-password', 'email': 'new@example.com'},
            token="JWT {0}".format(other_user.get_jwt_token())
        )

        self.assertEqual(response.status_code, 403)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'user@example.com')


class PasswordSetTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        super(PasswordSetTest, self).setUp()

        self.user = BlueBottleUserFactory.create(
            password='some-password',
            email='user@example.com'
        )
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.current_user_url = reverse('user-current')
        self.set_password_url = reverse('user-set-password')

    def test_update_paswword(self):
        response = self.client.put(
            self.set_password_url,
            {'password': 'some-password', 'new_password': 'new-password'},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue('jwt_token' in response.data)
        self.assertTrue('password' not in response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-password'))

        old_token_response = self.client.get(
            self.current_user_url, token=self.user_token
        )
        self.assertTrue(old_token_response.status_code, status.HTTP_403_FORBIDDEN)

        new_token_response = self.client.get(
            self.current_user_url, token='JWT {}'.format(response.data['jwt_token'])
        )
        self.assertTrue(new_token_response.status_code, status.HTTP_200_OK)

    def test_update_password_unauthenticated(self):
        response = self.client.put(
            self.set_password_url,
            {'password': 'some-password', 'new_password': 'new-password'},
        )

        self.assertEqual(response.status_code, 401)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('some-password'))

    def test_update_password_wrong_password(self):
        response = self.client.put(
            self.set_password_url,
            {'password': 'other-password', 'new_password': 'new-password'},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 403)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('some-password'))

    def test_update_password_short(self):
        response = self.client.put(
            self.set_password_url,
            {'password': 'some-password', 'new_password': '123456'},
            token=self.user_token
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(b'too short' in response.content)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('some-password'))

    def test_update_password_wrong_token(self):
        other_user = BlueBottleUserFactory.create(
            password='other-password'
        )

        response = self.client.put(
            self.set_password_url,
            {'password': 'some-password', 'new_password': 'new-password'},
            token="JWT {0}".format(other_user.get_jwt_token())
        )

        self.assertEqual(response.status_code, 403)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('some-password'))
        self.assertTrue(other_user.check_password('other-password'))


class UserLogoutTest(BluebottleTestCase):
    def setUp(self):
        super(UserLogoutTest, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.current_user_url = reverse('user-current')
        self.logout_url = reverse('user-logout')

    def test_get_profile(self):
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['email'], self.user.email)

    def test_logout(self):
        response = self.client.post(self.logout_url, token=self.user_token)
        self.assertEqual(response.status_code, 204)

        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.status_code, 401)

    def test_logout_no_token(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 401)

    def test_logout_wrong_token(self):
        response = self.client.post(self.logout_url, token=self.user_token + '1234')
        self.assertEqual(response.status_code, 401)


class UserActivityTest(BluebottleTestCase):
    def setUp(self):
        super(UserActivityTest, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.user_activity_url = reverse('user-activity')

    def test_log_activity(self):
        data = {'path': '/'}
        response = self.client.post(self.user_activity_url, data, token=self.user_token)
        self.assertEqual(response.status_code, 201)
        data = {'path': '/pages/about'}
        response = self.client.post(self.user_activity_url, data, token=self.user_token)
        self.assertEqual(response.status_code, 201)
        data = {'path': '/initiatives/activities/list'}
        response = self.client.post(self.user_activity_url, data, token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserActivity.objects.count(), 3)

    def test_log_activity_anonymous(self):
        data = {'path': '/'}
        response = self.client.post(self.user_activity_url, data)
        self.assertEqual(response.status_code, 401)

    def test_log_activity_long_path(self):
        data = {'path': '/' + ('a' * 300)}
        response = self.client.post(self.user_activity_url, data, token=self.user_token)
        self.assertEqual(response.status_code, 201)

        activity = UserActivity.objects.get()

        self.assertEqual(
            len(activity.path), 200
        )
        self.assertTrue(activity.path.startswith('/aaaaaaa'))


class PasswordStrengthDetailTest(BluebottleTestCase):
    def setUp(self):
        super(PasswordStrengthDetailTest, self).setUp()

        self.url = reverse('password-strength')
        self.client = JSONAPITestClient()
        self.data = {
            'data': {
                'type': 'password-strengths',
                'attributes': {
                    'email': 'admin@example.com',
                    'password': 'blabla',
                }
            }
        }

    def test_too_short(self):
        response = self.client.post(self.url, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        self.assertEqual(
            errors[0]['detail'],
            'This password is too short. It must contain at least 8 characters.'
        )

    def test_common(self):
        self.data['data']['attributes']['password'] = 'password'
        response = self.client.post(self.url, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        self.assertEqual(
            errors[0]['detail'],
            'This password is too common.'
        )

    def test_email(self):
        self.data['data']['attributes']['password'] = 'adminexample'
        response = self.client.post(self.url, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        self.assertEqual(
            errors[0]['detail'],
            'The password is too similar to the email address.'
        )

    def test_valid_fair(self):
        self.data['data']['attributes']['password'] = 'somepassword'
        response = self.client.post(self.url, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 201)
        data = response.json()['data']['attributes']
        self.assertTrue(data['strength'] < 0.25)

    def test_valid_string(self):
        self.data['data']['attributes']['password'] = '243AfecioIEOIj^%efw'
        response = self.client.post(self.url, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 201)
        data = response.json()['data']['attributes']
        self.assertTrue(data['strength'] > 0.5)


class RefreshTokenTest(BluebottleTestCase):
    def setUp(self):
        super().setUp()

        self.user = BlueBottleUserFactory.create()

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(self.user)
        payload['exp'] = datetime.utcnow() + properties.JWT_EXPIRATION_DELTA - timedelta(minutes=35)
        payload['orig_iat'] = timegm((datetime.now() - timedelta(minutes=35)).utctimetuple())

        token = jwt_encode_handler(payload)

        self.token = "JWT {0}".format(token)

        self.url = reverse('settings')

    def test_refresh(self):
        response = self.client.get(self.url, token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_token = response['Refresh-Token']

        response = self.client.get(reverse('user-current'), token=new_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], self.user.pk)


class UserAPITestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create()
        self.user_token = 'JWT {}'.format(self.user.get_jwt_token())
        self.current_user_url = reverse('user-current')
        self.segment_type = SegmentTypeFactory.create(required=False)
        self.segments = SegmentFactory.create_batch(3, segment_type=self.segment_type)

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.current_user_url = reverse('user-current')
        self.logout_url = reverse('user-logout')

    def test_get_current_user_no_required_segments(self):
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [])

    def test_get_current_user_required_location(self):
        settings = MemberPlatformSettings.load()
        settings.require_office = True
        settings.save()
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], ['location'])

    def test_get_current_user_required_fields(self):
        settings = MemberPlatformSettings.load()
        settings.require_address = True
        settings.require_phone_number = True
        settings.require_birthdate = True
        settings.save()
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertTrue('birthdate' in response.json()['required'])
        self.assertTrue('phone_number' in response.json()['required'])
        self.assertTrue('address' in response.json()['required'])

        self.user.birthdate = date(1980, 1, 14)
        self.user.phone_number = '+310612345678'
        self.user.place = PlaceFactory.create(
            street="test straat",
            street_number=12,
            postal_code='1024 BZ',
            locality="Amsterdam",
        )
        self.user.save()

        response = self.client.get(self.current_user_url, token=self.user_token)

        self.assertEqual(response.json()['required'], [])

    def test_get_current_user_required_location_set(self):
        settings = MemberPlatformSettings.load()
        settings.require_office = True
        settings.save()
        self.user.location = LocationFactory.create()
        self.user.save()
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [])

    def test_get_current_user_with_required_segments(self):
        self.segment_type.required = True
        self.segment_type.save()
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [f'segment_type.{self.segment_type.id}'])

    def test_get_current_user_with_required_segments_defined(self):
        self.segment_type.required = True
        self.segment_type.save()
        self.user.segments.add(self.segments[0], through_defaults={'verified': True})
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [])

    def test_get_current_user_with_unverified_required_segments(self):
        self.segment_type.required = True
        self.segment_type.needs_verification = True
        self.segment_type.save()
        self.user.segments.add(self.segments[0], through_defaults={'verified': False})
        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [f'segment_type.{self.segment_type.id}'])

    def test_get_current_user_with_unverified_required_location(self):
        MemberPlatformSettings.objects.update_or_create(
            require_office=True,
            verify_office=True,
        )
        self.user.location = LocationFactory.create()
        self.user.location_verified = False
        self.user.save()

        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], ['location'])

        self.user.location_verified = True
        self.user.save()

        response = self.client.get(self.current_user_url, token=self.user_token)
        self.assertEqual(response.json()['required'], [])
