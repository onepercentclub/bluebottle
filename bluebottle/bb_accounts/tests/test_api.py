import json
import re
import urlparse
import time

import mock

import httmock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.http import int_to_base36
from rest_framework import status

from bluebottle.members.tokens import login_token_generator

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (OrganizationFactory, OrganizationContactFactory,
                                                          OrganizationMemberFactory)
from bluebottle.test.factory_models.geo import LocationFactory, CountryFactory
from bluebottle.test.utils import BluebottleTestCase

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

        # User with partner organization
        self.user_with_partner_organization = BlueBottleUserFactory.create()
        self.user_with_partner_organization_token = "JWT {0}".format(self.user_with_partner_organization.get_jwt_token()
                                                                     )
        self.organization = OrganizationFactory.create(name='Partner Organization',
                                                       slug='partner-organization',
                                                       website='http://partnerorg.nl')
        self.organization_contact = OrganizationContactFactory.create(organization=self.organization)
        self.organization_member = OrganizationMemberFactory.create(organization=self.organization)
        self.user_with_partner_organization.partner_organization = self.organization
        self.user_with_partner_organization.save()

        self.current_user_api_url = reverse('user-current')
        self.manage_profile_url = reverse('manage-profile', args=(self.user_1.pk, ))
        self.user_create_api_url = reverse('user-user-create')
        self.user_password_reset_api_url = reverse('password-reset')

    def test_user_profile_returned_fields(self):
        user_profile_url = reverse('user-profile-detail', kwargs={'pk': self.user_1.id})
        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        serializer_fields = ['id', 'url', 'full_name', 'short_name', 'picture',
                             'primary_language', 'about_me', 'location',
                             'project_count', 'donation_count', 'date_joined',
                             'fundraiser_count', 'task_count', 'time_spent',
                             'website', 'twitter', 'facebook', 'skypename', 'partner_organization']

        for field in serializer_fields:
            self.assertTrue(field in response.data)

        excluded_fields = ['email', 'address', 'newsletter',
                           'campaign_notifications',
                           'birthdate', 'gender', 'first_name', 'last_name',
                           'password']

        for field in excluded_fields:
            self.assertFalse(field in response.data)

    def test_user_profile_not_from_facebook(self):
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})
        response = self.client.get(user_profile_url, token=self.user_1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['from_facebook'])

    def test_user_profile_from_facebook(self):
        self.user_1.social_auth.create(provider='facebook')
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})
        response = self.client.get(user_profile_url, token=self.user_1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['from_facebook'])

    def test_user_profile_returned_private_fields(self):
        group = Group.objects.get(name='Anonymous')
        group.permissions.remove(Permission.objects.get(codename='api_read_full_member'))

        user_profile_url = reverse('user-profile-detail', kwargs={'pk': self.user_2.id})
        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_2.id)

        # Fields taken from the serializer
        excluded_fields = ['last_name', 'avatar', 'about_me', 'twitter',
                           'facebook', 'skypename', 'picture', 'url',
                           'email', 'address', 'newsletter',
                           'campaign_notifications', 'phone_number',
                           'birthdate', 'gender', 'first_name', 'last_name',
                           'password']

        for field in excluded_fields:
            self.assertFalse(field in response.data)

    def test_user_profile_unauthenticated(self):
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})

        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_private_user_profile_returned_fields(self):
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})
        response = self.client.get(user_profile_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        serializer_fields = ['id', 'url', 'full_name', 'short_name', 'picture',
                             'primary_language', 'about_me', 'location',
                             'project_count', 'donation_count', 'date_joined',
                             'fundraiser_count', 'task_count', 'time_spent',
                             'website', 'twitter', 'facebook', 'skypename',
                             'email', 'phone_number',
                             'address', 'newsletter', 'campaign_notifications',
                             'birthdate', 'gender', 'first_name', 'last_name', 'partner_organization']
        for field in serializer_fields:
            self.assertTrue(field in response.data)

        self.assertEqual(response.data['partner_organization'], None)

    def test_user_with_partner_organization(self):
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_with_partner_organization.id})
        response = self.client.get(user_profile_url, token=self.user_with_partner_organization_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_with_partner_organization.id)

        self.assertTrue('partner_organization' in response.data)
        partner_organization_data = response.data['partner_organization']
        self.assertEqual(partner_organization_data['name'], 'Partner Organization')
        self.assertEqual(partner_organization_data['slug'], 'partner-organization')
        self.assertEqual(partner_organization_data['website'], 'http://partnerorg.nl')
        self.assertEqual(partner_organization_data['logo'], None)

    @override_settings(TOKEN_AUTH=ASSERTION_MAPPING)
    def test_user_profile_read_only_forbidden(self):
        """
        Test read only fields can't be updated.
        """
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})

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
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})

        email_field = {'email': 'user_allowed@onepercentclub.com'}

        # User should not be able to be updated read only fields in their profile.
        response = self.client.put(user_profile_url, email_field,
                                   token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         'Non-read-only profile fields are editable.')
        self.assertEqual(response.data['email'], 'user_allowed@onepercentclub.com')
        self.client.logout()

    def test_user_profile_retrieve_and_update(self):
        """
        Test retrieving a public user profile by id.
        """
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})
        response = self.client.get(user_profile_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_1.id)

        data = {
            'first_name': 'Nijntje',
            'last_name': 'het Konijntje',
            'address': {
                'line1': 'test line 1'
            }
        }

        # Profile should not be able to be updated by anonymous users.
        response = self.client.put(user_profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         response.data)

        # Profile should not be able to be updated by a different user.
        response = self.client.put(user_profile_url, data, token=self.user_2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Profile should be able to be updated by logged in user.
        response = self.client.put(user_profile_url, data, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], data['first_name'])
        self.assertEqual(response.data['last_name'], data['last_name'])
        self.assertEqual(response.data['address']['line1'], data['address']['line1'])

        self.client.logout()

    def test_user_profile_location_update(self):
        """
        Test that updating your location sets your country
        """
        country = CountryFactory.create()
        location = LocationFactory.create(country=country)
        user_profile_url = reverse('manage-profile', kwargs={'pk': self.user_1.id})
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
        response = self.client.get(self.current_user_api_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)
        self.assertEqual(response.data['last_name'], self.user_1.first_name)

        self.assertEqual(response.data['permissions']['project_list'],
                         {u'OPTIONS': True, u'GET': True})
        self.assertEqual(response.data['permissions']['project_manage_list'],
                         {u'GET': True, u'OPTIONS': True, u'POST': True})
        self.assertEqual(response.data['permissions']['homepage'],
                         {u'GET': True, u'OPTIONS': True})
        self.client.logout()

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_user_create(self):
        """
        Test creating a user with the api and activating the new user.
        """
        # Create a user.
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'test-password'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email, 'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        "JWT {0}".format(response.data['jwt_token'])

        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, [new_user_email])
        self.assertTrue('Take me there' in welcome_email.body)

    def test_user_create_required_email(self):
        response = self.client.post(self.user_create_api_url, {'password': 'test-password'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(response.data['email'][0], 'This field is required.')


    def test_user_create_invalid_password(self):
        """
        Test creating a user with the api and activating the new user.
        """
        # Create a user.
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'short'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email, 'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_user_create(self):
        """
        Test creating a user when a user already exists with the same email.
        """
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'test-password'

        user_1 = BlueBottleUserFactory.create(email=new_user_email)
        user_1.save()

        # Create a user.
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email, 'password': new_user_password})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        self.assertEqual(response.data['non_field_errors'][0]['type'], 'email')
        self.assertEqual(response.data['non_field_errors'][0]['email'], 'nijntje27@hetkonijntje.nl')
        self.assertEqual(
            unicode(response.data['non_field_errors'][0]['id']), unicode(user_1.pk)
        )
        self.assertEqual(
            unicode(response.data['email'][0]), 'member with this email address already exists.'
        )

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

        user = get_user_model().objects.get(email=new_user_email)

        self.assertEqual(user.username, new_user_email)

    def test_password_reset(self):
        # Setup: create a user.
        new_user_email = 'nijntje94@hetkonijntje.nl'
        new_user_password = 'password'
        response = self.client.post(self.user_create_api_url,
                                    {'email': new_user_email,
                                     'password': new_user_password})

        # Test: resetting the password should be allowed.
        response = self.client.put(self.user_password_reset_api_url, {'email': new_user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(mail.outbox), 1)

        # Setup: get the password reset token and url.
        c = re.compile(
            '\/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})\/',
            re.DOTALL)
        m = c.search(mail.outbox[0].body)
        password_set_url = reverse('password-set', kwargs={'uidb36': m.group(1), 'token': m.group(2)})

        # Test: check that non-matching passwords produce a validation error.
        passwords = {'new_password1': 'test-password', 'new_password2': 'test-passwordd'}
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)

        self.assertEqual(response.data['non_field_errors'][0],
                         "The two password fields didn't match.")

        # Test: check that updating the password works when the passwords match.
        passwords['new_password2'] = 'test-password'
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)

        # Test: check that trying to reuse the password reset link doesn't work.
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         response.data)

    def test_password_reset_validation(self):
        token = default_token_generator.make_token(self.user_1)       # Setup: create a user.
        uidb36 = int_to_base36(self.user_1.pk)
        password_set_url = reverse('password-set', kwargs={'uidb36': uidb36, 'token': token})

        # Test: check that non-matching passwords produce a validation error.
        passwords = {'new_password1': 'short', 'new_password2': 'short'}
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertTrue('This password is too short' in response.content)

    def test_deactivate(self):
        response = self.client.delete(
            self.manage_profile_url,
            token=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user_1.refresh_from_db()

        self.assertFalse(self.user_1.is_active)
        self.assertTrue(self.user_1.email.endswith('anonymous@example.com'))
        self.assertEqual(self.user_1.first_name, 'Deactivated')
        self.assertEqual(self.user_1.last_name, 'Member')

    def test_deactivate_no_token(self):
        response = self.client.delete(
            self.manage_profile_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.user_1.refresh_from_db()
        self.assertTrue(self.user_1.is_active)

    def test_deactivate_wrong_user(self):
        response = self.client.delete(
            self.manage_profile_url,
            token=self.user_2_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.user_1.refresh_from_db()
        self.assertTrue(self.user_1.is_active)


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


@httmock.urlmatch(netloc='www.google.com', path='/recaptcha/api/siteverify')
def captcha_mock(url, request):
    data = urlparse.parse_qs(request.body)
    if data.get('response')[0] == 'test-token':
        return json.dumps({'success': True})
    else:
        return {'content': json.dumps({'success': False}), 'status_code': 401}


@override_settings(RECAPTCHA_SECRET='test-secret')
class UserVerificationTest(BluebottleTestCase):
    """
    Test user verification view
    """

    def setUp(self):
        super(UserVerificationTest, self).setUp()
        self.user = BlueBottleUserFactory.create()

        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.verify_user_url = '/api/users/verification/'

    def test_verify(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                {'token': 'test-token'},
                token=self.user_token
            )
            self.assertEqual(response.status_code, 201)
            self.user.refresh_from_db()
            self.assertTrue(self.user.verified)

    def test_verify_unauthenticated(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                {'token': 'test-token'},
            )

            self.assertEqual(response.status_code, 401)

    def test_verify_no_token(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                token=self.user_token
            )

            self.assertEqual(response.status_code, 400)

    def test_verify_incorrect_token(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                {'token': 'incorrect-token'},
                token=self.user_token
            )

            self.assertEqual(response.status_code, 403)


class TokenLoginApiTest(BluebottleTestCase):
    def setUp(self):
        super(TokenLoginApiTest, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.other_user = BlueBottleUserFactory.create()

        self.token_login_url = reverse('token-login')

    def test_token_login(self):
        token = login_token_generator.make_token(self.user)
        response = self.client.post(
            self.token_login_url,
            data={'user_id': self.user.pk, 'token': token}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.keys(), ['token'])

    def test_token_login_twice(self):
        token = login_token_generator.make_token(self.user)
        self.client.post(
            self.token_login_url,
            data={'user_id': self.user.pk, 'token': token}
        )
        response = self.client.post(
            self.token_login_url,
            data={'user_id': self.user.pk, 'token': token}
        )

        self.assertEqual(response.status_code, 404)

    def test_token_missing_argument(self):
        token = login_token_generator.make_token(self.user)
        response = self.client.post(
            self.token_login_url,
            data={'token': token}
        )
        self.assertEqual(response.status_code, 400)

    def test_token_missing_user(self):
        token = login_token_generator.make_token(self.user)
        response = self.client.post(
            self.token_login_url,
            data={'user_id': '1234567890', 'token': token}
        )
        self.assertEqual(response.status_code, 404)

    def test_token_wrong_token(self):
        token = login_token_generator.make_token(self.user)
        response = self.client.post(
            self.token_login_url,
            data={'user_id': self.user.pk, 'token': token + '123'}
        )
        self.assertEqual(response.status_code, 404)

    def test_token_wrong_user(self):
        token = login_token_generator.make_token(self.user)
        response = self.client.post(
            self.token_login_url,
            data={'user_id': self.other_user.pk, 'token': token}
        )
        self.assertEqual(response.status_code, 404)

    def test_token_expired(self):
        past_time = time.time() - 35
        with mock.patch('django.core.signing.time.time', return_value=past_time):
            token = login_token_generator.make_token(self.user)

        response = self.client.post(
            self.token_login_url,
            data={'user_id': self.user.pk, 'token': token}
        )
        self.assertEqual(response.status_code, 404)
