from builtins import range
import time

import mock
from captcha import client
from django.core import mail
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.db import connection
from django.test.utils import override_settings
from rest_framework import status

from bluebottle.members.models import MemberPlatformSettings, UserActivity, Member
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        current_user_response = self.client.get(
            reverse('user-current'), token='JWT {}'.format(response.json()['token'])
        )

        self.assertEqual(current_user_response.status_code, status.HTTP_200_OK)

    def test_login_failed(self):
        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_failed_multiple(self):
        for i in range(0, 11):
            response = self.client.post(
                reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
            )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_failed_captcha(self):
        for i in range(0, 11):
            self.client.post(
                reverse('token-auth'), {'email': self.email, 'password': 'wrong'}
            )

        mock_response = client.RecaptchaResponse(True, extra_data={'hostname': 'testserver'})

        with mock.patch.object(client, 'submit', return_value=mock_response):
            captcha_response = self.client.post(
                reverse('captcha-verification'), {'token': 'test-token'}
            )

        self.assertEqual(captcha_response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse('token-auth'), {'email': self.email, 'password': self.password}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_create(self):
        email = 'test@example.com'
        connection.tenant.name = 'Test'
        connection.tenant.save()

        response = self.client.post(reverse('user-signup-token'), {'email': email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        member = Member.objects.get(email=email)
        self.assertTrue('{}:'.format(member.pk) in mail.outbox[0].body)
        self.assertEqual('Your activation link for Test', mail.outbox[0].subject)
        self.assertFalse(member.is_active)

    def test_create_twice(self):
        email = 'test@example.com'

        response = self.client.post(reverse('user-signup-token'), {'email': email})
        response = self.client.post(reverse('user-signup-token'), {'email': email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 2)

        member = Member.objects.get(email=email)
        self.assertFalse(member.is_active)

    def test_create_already_active(self):
        email = 'test@example.com'

        Member.objects.create(email=email, is_active=True)

        response = self.client.post(reverse('user-signup-token'), {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json()['email'][0], 'member with this email address already exists.')
        self.assertEqual(len(mail.outbox), 1)

    def test_create_correct_domain(self):
        email = 'test@example.com'
        self.settings.email_domain = 'example.com'
        self.settings.save()

        response = self.client.post(reverse('user-signup-token'), {'email': email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        member = Member.objects.get(email=email)
        self.assertFalse(member.is_active)

    def test_create_incorrect_domain(self):
        email = 'test@secondexample.com'
        self.settings.email_domain = 'example.com'
        self.settings.save()

        response = self.client.post(reverse('user-signup-token'), {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(
            'Only emails' in response.json()['email'][0]
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
            {'email': email, 'password': password, 'password_confirmation': password}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        member = Member.objects.get(email=email)

        self.assertEqual(member.is_active, True)
        self.assertTrue(member.check_password(password))

    def test_create_twice(self):
        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'password_confirmation': password}
        )
        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'password_confirmation': password}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['email'][0], 'member with this email address already exists.')

    def test_require_confirmation(self):
        self.settings.confirm_signup = True
        self.settings.save()

        email = 'test@example.com'
        password = 'test@example.com'

        response = self.client.post(
            reverse('user-user-create'),
            {'email': email, 'password': password, 'password_confirmation': password}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['token'][0], 'Signup requires a confirmation token')


@override_settings(SEND_WELCOME_MAIL=True)
class ConfirmSignUpTestCase(BluebottleTestCase):
    def setUp(self):
        (self.settings, _) = MemberPlatformSettings.objects.get_or_create()

        super(ConfirmSignUpTestCase, self).setUp()

    def test_confirm(self):
        email = 'test@example.com'
        password = 'test@example.com'

        member = Member.objects.create(email=email, is_active=False)
        mail.outbox = []

        response = self.client.put(
            reverse('user-signup-token-confirm', args=(TimestampSigner().sign(member.pk), )),
            {
                'password': password,
                'first_name': 'Tester',
                'last_name': 'de Test'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        member.refresh_from_db()

        self.assertEqual(member.is_active, True)
        self.assertTrue(member.check_password(password))
        self.assertEqual(member.first_name, 'Tester')
        self.assertEqual(member.last_name, 'de Test')

        profile_response = self.client.get(
            reverse('user-current'),
            token='JWT {}'.format(response.json()['jwt_token'])
        )
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to Test!')

    def test_confirm_twice(self):
        email = 'test@example.com'
        password = 'test@example.com'

        member = Member.objects.create(email=email, is_active=False)

        response = self.client.put(
            reverse('user-signup-token-confirm', args=(TimestampSigner().sign(member.pk), )),
            {
                'password': password,
                'first_name': 'Tester',
                'last_name': 'de Test'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(
            reverse('user-signup-token-confirm', args=(TimestampSigner().sign(member.pk), )),
            {
                'password': password,
                'first_name': 'Tester',
                'last_name': 'de Test'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['id'], 'The link to activate your account has already been used.')

    def test_confirm_expired_token(self):
        email = 'test@example.com'
        password = 'test@example.com'

        member = Member.objects.create(email=email, is_active=False)

        current_time = time.time()

        with mock.patch('time.time', return_value=current_time - (3 * 60 * 60)):
            token = TimestampSigner().sign(member.pk)

        response = self.client.put(
            reverse('user-signup-token-confirm', args=(token, )),
            {'password': password}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['id'], 'The link to activate your account has expired. Please sign up again.')

        member.refresh_from_db()

        self.assertEqual(member.is_active, False)
        self.assertFalse(member.check_password(password))

    def test_confirm_wrong_token(self):
        email = 'test@example.com'
        password = 'test@example.com'

        member = Member.objects.create(email=email, is_active=False)

        response = self.client.put(
            reverse(
                'user-signup-token-confirm',
                args=('{}:wrong-signature'.format(member.pk), )
            ),
            {'password': password}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['id'], 'Something went wrong on our side. Please sign up again.')

        member.refresh_from_db()

        self.assertEqual(member.is_active, False)
        self.assertFalse(member.check_password(password))


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
            {'password': 'other-password', 'new_password': 'new@example.com'},
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
