import json
import re

from django.core import mail
from django.test.utils import override_settings

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory, CountryFactory

ASSERTION_MAPPING = {
    'assertion_mapping': {
        'first_name': 'first_name_attr',
        'last_name': 'last_name_attr'
    }
}


class UserApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        super(UserApiIntegrationTest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()
        self.user_2_token = "JWT {0}".format(self.user_2.get_jwt_token())

        self.current_user_api_url = '/api/users/current'
        self.user_create_api_url = '/api/users/'
        self.user_profile_api_url = '/api/users/profiles/'
        self.user_private_profile_api_url = '/api/users/profiles/manage/'
        self.user_activation_api_url = '/api/users/activate/'
        self.user_password_reset_api_url = '/api/users/passwordreset'
        self.user_password_set_api_url = '/api/users/passwordset/'

    def test_user_profile_returned_fields(self):
        user_profile_url = "{0}{1}".format(self.user_profile_api_url,
                                           self.user_1.id)
        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        serializer_fields = ['id', 'url', 'full_name', 'short_name', 'picture',
                             'primary_language', 'about_me', 'location',
                             'project_count', 'donation_count', 'date_joined',
                             'fundraiser_count', 'task_count', 'time_spent',
                             'website', 'twitter', 'facebook', 'skypename', ]

        for field in serializer_fields:
            self.assertTrue(field in response.data)

        excluded_fields = ['email', 'address', 'newsletter',
                           'campaign_notifications',
                           'birthdate', 'gender', 'first_name', 'last_name',
                           'username', 'password']

        for field in excluded_fields:
            self.assertFalse(field in response.data)

    def test_user_profile_unauthenticated(self):
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)
        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_private_user_profile_returned_fields(self):
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)
        response = self.client.get(user_profile_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        serializer_fields = ['id', 'url', 'full_name', 'short_name', 'picture',
                             'primary_language', 'about_me', 'location',
                             'project_count', 'donation_count', 'date_joined',
                             'fundraiser_count', 'task_count', 'time_spent',
                             'website', 'twitter', 'facebook', 'skypename',
                             'email',
                             'address', 'newsletter', 'campaign_notifications',
                             'birthdate', 'gender', 'first_name', 'last_name',
                             'username']

        for field in serializer_fields:
            self.assertTrue(field in response.data)

    @override_settings(TOKEN_AUTH=ASSERTION_MAPPING)
    def test_user_profile_read_only_forbidden(self):
        """
        Test read only fields can't be updated.
        """
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)

        full_name = {'first_name': 'Nijntje', 'last_name': 'het Konijntje'}

        # User should not be able to be updated read only fields in their profile.
        response = self.client.put(user_profile_url, full_name,
                                   token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Read-only profile fields should not be editable.')

        self.client.logout()

    @override_settings(TOKEN_AUTH=ASSERTION_MAPPING)
    def test_user_profile_read_only_allowed(self):
        """
        Test other fields can be updated when tenant has read-only fields.
        """
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)

        email_field = {'email': 'user_allowed@onepercentclub.com'}

        # User should not be able to be updated read only fields in their profile.
        response = self.client.put(user_profile_url, email_field,
                                   token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Non-read-only profile fields are editable.')

        self.client.logout()

    def test_user_profile_retrieve_and_update(self):
        """
        Test retrieving a public user profile by id.
        """
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)
        response = self.client.get(user_profile_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_1.id)

        full_name = {'first_name': 'Nijntje', 'last_name': 'het Konijntje'}

        # Profile should not be able to be updated by anonymous users.
        response = self.client.put(user_profile_url, full_name)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         response.data)

        # Profile should not be able to be updated by a different user.
        response = self.client.put(user_profile_url, full_name,
                                   token=self.user_2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         response.data)

        # Profile should be able to be updated by logged in user.
        response = self.client.put(user_profile_url, full_name,
                                   token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['first_name'],
                         full_name.get('first_name'))
        self.assertEqual(response.data['last_name'], full_name.get('last_name'))

        self.client.logout()

    def test_user_profile_location_update(self):
        """
        Test that updating your location sets your country
        """
        country = CountryFactory.create()
        location = LocationFactory.create(country=country)
        user_profile_url = "{0}{1}".format(self.user_private_profile_api_url,
                                           self.user_1.id)
        changes = {'location': location.id}

        # Profile should not be able to be updated by anonymous users.
        response = self.client.put(user_profile_url, changes,
                                   token=self.user_1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(country.id, response.data['address']['country'])


    def test_unauthenticated_user(self):
        """
        Test retrieving the currently logged in user while not logged in.
        """
        # Test unauthenticated user doesn't return 500 error.
        response = self.client.get(self.current_user_api_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         response.data)

    def test_current_user(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.current_user_api_url,
                                   token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)

        self.client.logout()

    def test_user_create(self):
        """
        Test creating a user with the api and activating the new user.
        """
        # Create a user.
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'testing'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email,
                                     'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        token = "JWT {0}".format(response.data['jwt_token'])
        user_id = response.data['id']

        # Test that the email field is required on user create.
        response = self.client.post(self.user_create_api_url,
                                    {'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertEqual(response.data['email'][0], 'This field is required.')

    def test_duplicate_user_create(self):
        """
        Test creating a user when a user already exists with the same email.
        """
        user_1 = BlueBottleUserFactory.create(email='nijntje27@hetkonijntje.nl')
        user_1.save()

        # Create a user.
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'testing'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email,
                                     'password': new_user_password})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)

        self.assertEqual(response.data['non_field_errors'][0]['type'], 'email')
        self.assertEqual(response.data['non_field_errors'][0]['email'], 'nijntje27@hetkonijntje.nl')
        self.assertEqual(response.data['non_field_errors'][0]['id'], user_1.pk)
        self.assertEqual(response.data['email'][0], 'Member with this email address already exists.')

    def test_generate_username(self):
        new_user_email = 'nijntje74@hetkonijntje.nl'
        first_name = 'Nijntje'
        last_name = 'het Konijntje'
        new_user_password = 'password'

        # Test username generation with duplicates.
        response = self.client.post(self.user_create_api_url,
                                    {'first_name': first_name,
                                     'last_name': last_name,
                                     'email': new_user_email,
                                     'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEqual(response.data['username'], new_user_email)

    def test_password_reset(self):
        # Setup: create a user.
        new_user_email = 'nijntje94@hetkonijntje.nl'
        new_user_password = 'password'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email,
                                     'password': new_user_password})
        token = "JWT {0}".format(response.data['jwt_token'])
        user_id = response.data['id']

        # Test: resetting the password should be allowed.
        response = self.client.put(self.user_password_reset_api_url,
                                   {'email': new_user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(len(mail.outbox), 1)

        # Setup: get the password reset token and url.
        c = re.compile(
            '\/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})\/',
            re.DOTALL)
        m = c.search(mail.outbox[0].body)
        password_set_url = '{0}{1}-{2}'.format(self.user_password_set_api_url,
                                               m.group(1), m.group(2))

        # Test: check that non-matching passwords produce a validation error.
        passwords = {'new_password1': 'rabbit', 'new_password2': 'rabbitt'}
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)

        self.assertEqual(json.loads(response.content)['non_field_errors'][0],
                         "The two password fields didn't match.")

        # Test: check that updating the password works when the passwords match.
        passwords['new_password2'] = 'rabbit'
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)

        # Test: check that trying to reuse the password reset link doesn't work.
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         response.data)


class UnauthLocaleMiddlewareTest(BluebottleTestCase):
    """
    Integration tests for locale middleware when user unauthenticated.
    """
    @override_settings(LANGUAGES=(
        ('nl', 'Dutch'),
        ('en', 'English'),
    ))
    def test_redirect_to_browser_language(self):
        # test redirected to supported browser language
        http_languages = 'de-DE,de;q=0.8,nl;q=0.6,en;q=0.4,en-US;q=0.2'
        response = self.client.get('/', follow=False,
                                   HTTP_ACCEPT_LANGUAGE=http_languages)
        self.assertRedirects(response, '/nl/')

    @override_settings(LANGUAGES=(
        ('nl', 'Dutch'),
        ('en', 'English'),
    ))
    def test_redirect_to_unsupported_browser_language(self):
        # test redirected to default language
        http_languages = 'de-DE,de;q=0.8,es;q=0.6'
        response = self.client.get('/', follow=False,
                                   HTTP_ACCEPT_LANGUAGE=http_languages)
        self.assertRedirects(response, '/en/')

    def test_redirect_for_cookie(self):
        # test redirect to language set in cookie

        # go directly to supported language
        response = self.client.get('/nl/', follow=False)
        self.assertTrue(response.status_code, 200)

        # go to base path => redirected to langauge in cookie
        response = self.client.get('/', follow=False)
        self.assertRedirects(response, '/nl/')
        self.assertEqual(self.client.cookies['django_language'].value, 'nl')

    @override_settings(LANGUAGES=(
        ('nl', 'Dutch'),
        ('en', 'English'),
    ))
    def test_redirect_for_anonymous_user_unsupported_language(self):
        response = self.client.get('/es/', follow=False)
        self.assertRedirects(response, '/en/')

    def test_no_redirect_for_anonymous_user(self):
        response = self.client.get('/nl/', follow=False)
        self.assertTrue(response.status_code, 200)


class AuthLocaleMiddlewareTest(BluebottleTestCase):
    """
    Integration tests for locale middleware when user is authenticated.
    """

    def setUp(self):
        super(AuthLocaleMiddlewareTest, self).setUp()

        self.user_en = BlueBottleUserFactory.create()
        self.user_en.primary_language = 'en'
        self.user_en.save()
        self.user_en_token = "JWT {0}".format(self.user_en.get_jwt_token())

        self.user_nl = BlueBottleUserFactory.create()
        self.user_nl.primary_language = 'nl'
        self.user_nl.save()
        self.user_nl_token = "JWT {0}".format(self.user_nl.get_jwt_token())

        self.user_es = BlueBottleUserFactory.create()
        self.user_es.primary_language = 'es'
        self.user_es.save()
        self.user_es_token = "JWT {0}".format(self.user_es.get_jwt_token())

    @override_settings(LANGUAGES=(
        ('nl', 'Dutch'),
        ('en', 'English'),
    ))
    def test_redirect_to_primary_for_unsupported_language(self):
        # test redirected to users primary language
        response = self.client.get('/de/', follow=False,
                                   token=self.user_nl_token)
        self.assertRedirects(response, '/nl/')

    @override_settings(LANGUAGES=(
        ('nl', 'Dutch'),
        ('en', 'English'),
    ))
    def test_redirect_to_default_for_unsupported_language(self):
        # test redirected to default language if users language
        # is not supported on platform
        response = self.client.get('/es/', follow=False,
                                   token=self.user_es_token)
        self.assertRedirects(response, '/en/')

    def test_no_redirect_for_supported_language(self):
        response = self.client.get('/nl/', follow=False,
                                   token=self.user_en_token)
        self.assertTrue(response.status_code, 200)

    def test_no_redirect_for_non_language_urls(self):
        response = self.client.get('/api/', follow=False,
                                   token=self.user_en_token)
        self.assertTrue(response.status_code, 200)

        response = self.client.get('/', follow=False, token=self.user_en_token)
        self.assertTrue(response.status_code, 200)


class UserProfileUpdateTests(BluebottleTestCase):
    """
    Integration tests for the User API with dependencies on different bluebottle apps.
    """

    def setUp(self):
        super(UserProfileUpdateTests, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_2 = BlueBottleUserFactory.create()
        self.current_user_api_url = '/api/users/current'
        self.user_create_api_url = '/api/users/'
        self.user_profile_api_url = '/api/users/profiles/'
        self.user_activation_api_url = '/api/users/activate/'
        self.user_password_reset_api_url = '/api/users/passwordreset'
        self.user_password_set_api_url = '/api/users/passwordset/'
