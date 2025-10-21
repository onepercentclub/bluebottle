from future import standard_library

from bluebottle.members.models import MemberPlatformSettings, SocialLoginSettings
standard_library.install_aliases()
import json

import mock
import httmock

from django.urls import reverse
from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


@httmock.urlmatch(netloc='graph.facebook.com', path='/[v0-9\.]+/me')
def facebook_me_mock(url, request):
    return json.dumps({'first_name': 'First', 'last_name': 'Last', 'email': 'test@goodup.com'})


def load_signed_request_mock(self, signed_request):
    _key, secret = self.get_key_and_secret()

    if signed_request == 'test-signed-request' and secret == 'test-secret':
        return {'user_id': 1}
    else:
        return {}


class SocialTokenAPITestCase(BluebottleTestCase):
    """
    Test the social authorization token api endpoint
    """

    def setUp(self):
        super(SocialTokenAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.token_url = reverse('social-login')
        self.client = JSONAPITestClient()

        settings = MemberPlatformSettings.load()

        self.settings = SocialLoginSettings(
            secret='test-secret',
            client_id='test-client-id',
            backend='facebook',
            settings=settings
        )
        self.settings.save()

    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    'data': {
                        'type': 'social/tokens',

                        'attributes': {
                            'backend': 'facebook',
                            'access-token': 'test_token',
                            'signed-request': 'test-signed-request'
                        }
                    }
                },
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue('token' in response.json()['data']['attributes'])

            authenticated_response = self.client.get(
                reverse('current-member-detail'),
                HTTP_AUTHORIZATION="JWT {0}".format(response.json()['data']['attributes']['token'])
            )

            self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                authenticated_response.json()['data']['attributes']['first-name'],
                'First'
            )
            self.assertEqual(
                authenticated_response.json()['data']['attributes']['last-name'],
                'Last'
            )

    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_signed_request(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    'type': 'social/tokens',
                    'attributes': {
                        'backend': 'facebook',
                        'access-token': 'test_token',
                        'signed-request': 'test-invalid'
                    }
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_secret(self):
        self.settings.secret = 'invalid-secret'
        self.settings.save()

        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    'type': 'social/tokens',
                    'attributes': {
                        'backend': 'facebook',
                        'access-token': 'test_token',
                        'signed-request': 'test-signed-request'
                    }
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_token(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(
                self.token_url,
                {
                    'type': 'social/tokens',
                    'attributes': {
                        'backend': 'facebook',
                        'access-token': 'test_invalid_token',
                        'signed-request': 'test-signed-request'
                    }
                },
                token=self.user_token)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_no_data(self):
        with httmock.HTTMock(facebook_me_mock):
            response = self.client.post(self.token_url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
