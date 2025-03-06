from future import standard_library
standard_library.install_aliases()

from builtins import str
import json
import re
import urllib.parse

import httmock

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.test.utils import override_settings
from django.utils.http import int_to_base36
from rest_framework import status

from bluebottle.members.models import MemberPlatformSettings, UserSegment

from bluebottle.segments.tests.factories import SegmentFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory, OrganizationContactFactory
)

from bluebottle.test.factory_models.geo import PlaceFactory, LocationFactory
from bluebottle.test.utils import BluebottleTestCase, APITestCase, JSONAPITestClient

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
        self.client = JSONAPITestClient()

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
        self.organization_contact = OrganizationContactFactory.create()
        self.user_with_partner_organization.partner_organization = self.organization
        self.user_with_partner_organization.save()

        self.current_user_api_url = reverse('user-current')
        self.profile_url = reverse('member-profile-detail', args=(self.user_1.pk, ))
        self.profile_url_with_partner_organization = reverse(
            'member-profile-detail', args=(self.user_with_partner_organization.pk, )
        )
        self.user_create_api_url = reverse('member-signup')
        self.user_password_reset_api_url = reverse('password-reset')

    def test_user_profile_returned_fields(self):
        response = self.client.get(self.profile_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        attributes = [
            'first-name', 'last-name', 'about-me', 'full-name', 'required',
            'birthdate', 'phone-number', 'email', 'search-distance',
            'any-search-distance', 'exclude-online', 'matching-options-set',
            'remote-id', 'subscribed', 'receive-reminder-emails',
            'campaign-notifications', 'has-usable-password'
        ]
        for field in attributes:
            self.assertTrue(
                field in response.json()['data']['attributes'],
                "Missing field {}".format(field)
            )

        relationships = [
            'segments', 'location', 'place', 'themes', 'skills', 'avatar'
        ]
        for field in relationships:
            self.assertTrue(
                field in response.json()['data']['relationships'],
                "Missing field {}".format(field)
            )

    def test_user_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_detail_unauthenticated(self):
        user_profile_url = reverse('user-profile-detail', kwargs={'pk': self.user_1.id})

        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_detail_unauthenticated_closed(self):
        user_profile_url = reverse('user-profile-detail', kwargs={'pk': self.user_1.id})
        MemberPlatformSettings.objects.update_or_create(
            closed=True,
        )

        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_private_user_profile_returned_fields(self):
        response = self.client.get(self.profile_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_1.id)

        # Fields taken from the serializer
        fields = [
            'first-name', 'last-name', 'about-me', 'full-name', 'required',
            'birthdate', 'phone-number', 'email', 'search-distance',
            'any-search-distance', 'exclude-online', 'matching-options-set',
            'remote-id', 'subscribed', 'receive-reminder-emails',
            'campaign-notifications', 'has-usable-password',
        ]

        attributes = response.json()['data']['attributes']
        for field in fields:
            self.assertTrue(field in attributes, "Missing field {}".format(field))

    def test_user_with_partner_organization(self):
        response = self.client.get(
            self.profile_url_with_partner_organization,
            HTTP_AUTHORIZATION=self.user_with_partner_organization_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.user_with_partner_organization.id)

    @override_settings(TOKEN_AUTH=ASSERTION_MAPPING)
    def test_user_profile_update_email_not_allowed(self):
        """
        Test other fields can be updated when tenant has read-only fields.
        """
        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'data': {
                    'attributes': {
                        'email': 'new@example.com'
                    }
                }
            }
        }

        # User should not be able to be updated read only fields in their profile.
        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['data']['attributes']['email'], self.user_1.email
        )

    def test_user_profile_retrieve_and_update(self):
        """
        Test retrieving a public user profile by id.
        """
        response = self.client.get(self.profile_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_1.id)
        self.assertEqual(response.data['subscribed'], False)

        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'attributes': {
                    'first_name': 'Nijntje',
                    'last_name': 'het Konijntje',
                    'subscribed': True
                }
            }
        }

        # Profile should not be able to be updated by anonymous users.
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         response.data)

        # Profile should not be able to be updated by a different user.
        response = self.client.put(self.profile_url, data, HTTP_AUTHORIZATION=self.user_2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Profile should be able to be updated by logged in user.
        response = self.client.patch(self.profile_url, data, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.json()['data']['attributes']['first-name'], 'Nijntje'
        )
        self.assertEqual(
            response.json()['data']['attributes']['last-name'], 'het Konijntje'
        )

    def test_user_update_place(self):
        """
        Test updating a user with the api and setting a place.
        """
        # Create a user.
        place = PlaceFactory.create(
            content_object=self.user_1
        )

        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'relationships': {
                    'place': {
                        'data': {'id': place.pk, 'type': 'places'}
                    }
                }
            }
        }
        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.json()['data']['relationships']['place']['data']['id'],
            str(place.pk)
        )

    def test_user_delete_place(self):
        """
        Test updating a user with the api and setting a place.
        """
        self.test_user_update_place()

        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'relationships': {
                    'place': {
                        'data': None
                    }
                }
            }
        }

        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user_1.refresh_from_db()
        self.assertIsNone(
            self.user_1.place
        )

    def test_user_set_segment(self):
        """
        Test updating a user with the api and setting a place.
        """

        segment = SegmentFactory.create()
        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'relationships': {
                    'segments': {
                        'data': [{'id': segment.pk, 'type': 'segments'}]
                    }
                }
            }
        }

        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.json()['data']['relationships']['segments']['data'][0]['id'],
            str(segment.pk)
        )
        self.assertEqual(self.user_1.segments.first(), segment)

    def test_user_verify_segment(self):
        """
        Test updating a user with the api and setting a place.
        """

        segment = SegmentFactory.create()
        self.user_1.segments.add(segment, through_defaults={'verified': False})
        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'relationships': {
                    'segments': {
                        'data': [
                            {'id': segment.pk, 'type': 'segments'}
                        ]
                    }
                }
            }
        }

        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.json()['data']['relationships']['segments']['data'][0]['id'],
            str(segment.pk)
        )
        self.assertEqual(self.user_1.segments.first(), segment)
        self.assertTrue(UserSegment.objects.get(member=self.user_1, segment=segment).verified)

    def test_user_verify_location(self):
        """
        Test updating a user with the api and setting a place.
        """
        MemberPlatformSettings.objects.update_or_create(
            verify_office=True,
        )

        self.user_1.location = LocationFactory.create()
        self.user_1.location_verified = False
        self.user_1.save()

        new_location = LocationFactory.create()
        data = {
            'data': {
                'id': self.user_1.pk,
                'type': 'member/profile',
                'relationships': {
                    'location': {
                        'data': {'id': new_location.pk, 'type': 'locations'}
                    }
                }
            }
        }

        response = self.client.patch(
            self.profile_url,
            data,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            response.json()['data']['relationships']['location']['data']['id'],
            str(new_location.pk)
        )

        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.location, new_location)
        self.assertTrue(self.user_1.location_verified)

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
        response = self.client.get(self.current_user_api_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)
        self.assertEqual(response.data['last_name'], self.user_1.first_name)

        self.assertEqual(response.data['permissions']['project_list'],
                         {u'OPTIONS': True, u'POST': True})
        self.assertEqual(response.data['permissions']['homepage'],
                         {u'GET': True, u'OPTIONS': True})
        self.client.logout()

    def test_current_user_url_variations(self):
        response = self.client.get('/api/users/current', HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        response = self.client.get('/api/users/current/', HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_logout_authenticated(self):
        """
        Test logout of authenticated user
        """

        response = self.client.post(reverse('user-logout'), HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_logout_unauthenticated(self):
        """
        Test logout of unauthenticated user
        """

        response = self.client.post(reverse('user-logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)

    def test_current_user_organization(self):
        """
        Test retrieving the currently logged in user with partner organization
        """
        organization = OrganizationFactory.create(name='GoodUp')
        self.user_1.partner_organization = organization
        self.user_1.save()
        response = self.client.get(self.current_user_api_url, HTTP_AUTHORIZATION=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['organization']['name'], 'GoodUp')

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_user_create(self):
        """
        Test creating a user with the api and activating the new user.
        """
        mail.outbox = []

        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'test-password'
                }
            }
        }
        response = self.client.post(
            self.user_create_api_url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        welcome_email = mail.outbox[0]
        self.assertEqual(welcome_email.to, ['nijntje27@hetkonijntje.nl'])
        self.assertTrue("[Take me there](https://testserver?" in welcome_email.body)

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_user_create_closed_site(self):
        """
        Test creating a user with the api and activating the new user.
        """
        MemberPlatformSettings.objects.update_or_create(closed=True)

        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'test-password'
                }
            }
        }

        response = self.client.post(
            self.user_create_api_url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_user_create_required_email(self):
        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'password': 'test-password'
                }
            }
        }
        response = self.client.post(self.user_create_api_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(
            response.json()['errors'][0]['detail'], 'This field is required.'
        )

    def test_user_create_invalid_password(self):
        """
        Test creating a user with the api and activating the new user.
        """
        # Create a user.
        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'short'
                }
            }
        }
        response = self.client.post(
            self.user_create_api_url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['errors'][0]['code'], 'password_too_short')

    def test_duplicate_user_create(self):
        """
        Test creating a user when a user already exists with the same email.
        """
        new_user_email = 'nijntje27@hetkonijntje.nl'

        user_1 = BlueBottleUserFactory.create(email=new_user_email)
        user_1.save()

        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'short'
                }
            }
        }
        # Create a user.
        response = self.client.post(
            self.user_create_api_url,
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(
            response.json()['errors'][0]['detail'],
            'A user with this email address already exists'
        )

    def test_password_reset(self):
        # Setup: create a user.
        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'some-password'
                }
            }
        }
        response = self.client.post(
            self.user_create_api_url, data
        )

        # Test: resetting the password should be allowed.
        response = self.client.post(
            self.user_password_reset_api_url,
            {
                'data': {
                    'attributes': {
                        'email': 'nijntje27@hetkonijntje.nl'
                    },
                    'type': 'reset-tokens'
                }
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(mail.outbox), 1)

        self.assertTrue('/auth/set-password' in mail.outbox[0].body)

        # Setup: get the password reset token and url.
        token_regex = re.compile(
            '\?token=(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})',
            re.DOTALL)
        token_matches = token_regex.search(mail.outbox[0].body)
        reset_confirm_url = reverse('password-reset-confirm')

        attributes = {'password': 'test-password', 'token': f'{token_matches[1]}-{token_matches[2]}'}

        response = self.client.post(
            reset_confirm_url,
            {'data': {'attributes': attributes, 'type': 'reset-token-confirmations'}},
        )
        confirm_data = response.json()['data']
        self.assertTrue('id' in confirm_data)
        self.assertTrue('token' in confirm_data['attributes'])
        self.assertTrue('jwt-token' in confirm_data['attributes'])
        self.assertTrue('password' in confirm_data['attributes'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)

        # Test: check that trying to reuse the password reset link doesn't work.
        response = self.client.post(
            reset_confirm_url,
            {'data': {'attributes': attributes, 'type': 'reset-token-confirmations'}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_rate_limit(self):
        # Setup: create a user.
        data = {
            'data': {
                'type': 'auth/signup',
                'attributes': {
                    'email': 'nijntje27@hetkonijntje.nl',
                    'password': 'some-password'
                }
            }
        }
        response = self.client.post(
            self.user_create_api_url, data
        )

        for _ in range(12):
            response = self.client.post(
                self.user_password_reset_api_url,
                {
                    'data': {
                        'attributes': {
                            'email': 'nijntje27@hetkonijntje.nl'
                        },
                        'type': 'reset-tokens'
                    }
                }
            )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_password_reset_inactive(self):
        # Setup: create a user.
        client = JSONAPITestClient()

        user = BlueBottleUserFactory.create(is_active=False)

        response = client.post(
            self.user_password_reset_api_url,
            {'data': {'attributes': {'email': user.email}, 'type': 'reset-tokens'}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_validation(self):
        client = JSONAPITestClient()
        token = default_token_generator.make_token(self.user_1)       # Setup: create a user.
        uidb36 = int_to_base36(self.user_1.pk)
        reset_confirm_url = reverse('password-reset-confirm')

        # Test: check that short passwords produce a validation error.
        attributes = {'password': 'short', 'token': f'{uidb36}-{token}'}

        response = client.post(
            reset_confirm_url,
            {'data': {'attributes': attributes, 'type': 'reset-token-confirmations'}},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(b'Password should at least be 8 characters.' in response.content)

    def test_deactivate(self):
        response = self.client.delete(
            self.profile_url,
            HTTP_AUTHORIZATION=self.user_1_token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user_1.refresh_from_db()

        self.assertFalse(self.user_1.is_active)
        self.assertTrue(self.user_1.email.endswith('anonymous@example.com'))
        self.assertEqual(self.user_1.first_name, 'Deactivated')
        self.assertEqual(self.user_1.last_name, 'Member')

    def test_deactivate_no_token(self):
        response = self.client.delete(
            self.profile_url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.user_1.refresh_from_db()
        self.assertTrue(self.user_1.is_active)

    def test_deactivate_wrong_user(self):
        response = self.client.delete(
            self.profile_url,
            HTTP_AUTHORIZATION=self.user_2_token
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
                                   HTTP_AUTHORIZATION=self.user_en_token)
        self.assertTrue(response.status_code, 200)

    def test_no_redirect_for_non_language_urls(self):
        response = self.client.get('/api/', follow=False,
                                   HTTP_AUTHORIZATION=self.user_en_token)
        self.assertTrue(response.status_code, 200)

        response = self.client.get('/', follow=False, HTTP_AUTHORIZATION=self.user_en_token)
        self.assertTrue(response.status_code, 200)


@httmock.urlmatch(netloc='www.google.com', path='/recaptcha/api/siteverify')
def captcha_mock(url, request):
    data = urllib.parse.parse_qs(request.body)
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
        self.verify_user_url = reverse('user-verification')

    def test_verify(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                {'token': 'test-token'},
                HTTP_AUTHORIZATION=self.user_token
            )
            self.assertEqual(response.status_code, 201)
            self.user.refresh_from_db()
            self.assertTrue(self.user.verified)
            self.assertEqual(response.data, {'token': u'test-token', 'id': self.user.id})

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
                HTTP_AUTHORIZATION=self.user_token
            )

            self.assertEqual(response.status_code, 400)

    def test_verify_incorrect_token(self):
        with httmock.HTTMock(captcha_mock):
            response = self.client.post(
                self.verify_user_url,
                {'token': 'incorrect-token'},
                HTTP_AUTHORIZATION=self.user_token
            )

            self.assertEqual(response.status_code, 403)


class MemberDetailViewAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user1 = BlueBottleUserFactory()
        self.user2 = BlueBottleUserFactory()
        self.model = self.user1
        self.url = reverse('member-detail', args=(self.user1.id,))

    def test_get_current_user(self):
        self.perform_get(user=self.user1)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(self.response.data['id'], self.user1.id)

    def test_get_other_user(self):
        self.perform_get(user=self.user2)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(self.response.data['id'], self.user1.id)


class LoginJsonApiTestCase(BluebottleTestCase):

    def setUp(self):
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory(password='psssssst')
        self.url = reverse('auth')
        self.data = {
            'data': {
                'attributes': {
                    'email': self.user.email,
                    'password': 'psssssst'
                },
                'type': "auth/token"
            },
        }

    def test_login_wrong_pwd(self):
        expected = {
            'errors': [{
                'code': 'invalid',
                'detail': 'Unable to log in with provided credentials.',
                'source': {
                    'pointer': '/data'
                },
                'status': '400'
            }]
        }
        self.data['data']['attributes']['password'] = 'awildguess'
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(expected, data)

    def test_login_pwd_null(self):
        expected = {
            'errors': [{
                'code': 'null',
                'detail': 'This field may not be null.',
                'source': {
                    'pointer': '/data/attributes/password'
                },
                'status': '400'
            }]
        }
        self.data['data']['attributes']['password'] = None
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(expected, data)

    def test_login_pwd_empty(self):
        expected = {
            'errors': [{
                'code': 'blank',
                'detail': 'This field may not be blank.',
                'source': {
                    'pointer': '/data/attributes/password'
                },
                'status': '400'
            }]
        }
        self.data['data']['attributes']['password'] = ''
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(expected, data)

    def test_login_too_many_failed_attempts(self):
        expected = {
            'errors': [{
                'code': 'throttled',
                'detail': 'Too many failed password attempts. Expected available in 600 seconds.',
                'source': {
                    'pointer': '/data'
                },
                'status': '429'
            }]
        }
        self.data['data']['attributes']['password'] = 'awildguess'
        for i in range(10):
            self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertEqual(expected, data)


class UserSignupTokenApiTestCase(BluebottleTestCase):

    def setUp(self):
        self.client = JSONAPITestClient()
        self.url = reverse('user-signup-token')
        self.data = {
            'data': {
                'attributes': {
                    'email': 'malle@eppie.hh',
                },
                'type': "signup-tokens"
            },
        }

    def test_create_user(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNotNone(data['data']['id'])

    def test_existing__user(self):
        user = BlueBottleUserFactory.create()
        self.data['data']['attributes']['email'] = user.email
        expected = {
            'errors': [{
                'code': 'email_in_use',
                'detail': 'A member with this email address already exists.',
                'source': {
                    'pointer': '/data/attributes/email'
                },
                'status': '400'
            }]
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(expected, data)

    def test_existing_inactive_user(self):
        user = BlueBottleUserFactory.create(is_active=False)
        self.data['data']['attributes']['email'] = user.email
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['id'], str(user.id))
