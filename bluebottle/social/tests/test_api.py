import json

import mock
import httmock

from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


@httmock.urlmatch(netloc='graph.facebook.com', path='/v2.3/me')
def facebook_me_mock(url, request):
    return json.dumps({'firstname': 'bla', 'lastname': 'bla'})


@httmock.urlmatch(netloc='graph.facebook.com', path='/v2.3/oauth/access_token')
def facebook_access_token(url, request):
    return json.dumps({})


@httmock.urlmatch(netloc='graph.facebook.com', path='/me/permissions')
def facebook_me_permissions_mock(url, request):
    if request.headers['authorization'] == 'Bearer test_token':
        return json.dumps({"data": [{"permission": "publish_actions", "status": "granted"}]})
    else:
        content = json.dumps({'error': 'invalid token'})
        return {'content': content, 'status_code': status.HTTP_401_UNAUTHORIZED}


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

        self.token_url = reverse('access-token', kwargs={'backend': 'facebook'})

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-secret'):
            with httmock.HTTMock(facebook_me_mock,
                                 facebook_me_permissions_mock,
                                 facebook_access_token):
                response = self.client.post(
                    self.token_url,
                    {
                        'access_token': 'test_token',
                        'signed_request': 'test-signed-request'
                    },
                    token=self.user_token
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(json.loads(response.content), {})

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_signed_request(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-secret'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_me_mock):
                    response = self.client.post(
                        self.token_url,
                        {
                            'signed_request': 'test-invalid',
                            'access_token': 'test-token'
                        },
                        token=self.user_token)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_secret(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_me_mock,
                                     facebook_access_token):
                    response = self.client.post(
                        self.token_url,
                        {
                            'signed_request': 'test-signed-request',
                            'access_token': 'test-token'
                        },
                        token=self.user_token)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_invalid_token(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-secret'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_me_mock,
                                     facebook_access_token,
                                     facebook_me_permissions_mock):
                    response = self.client.post(
                        self.token_url,
                        {
                            'signed_request': 'test-signed-request',
                            'access_token': 'invalid-token'
                        },
                        token=self.user_token)
                    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_unauthenticated(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_me_mock):
                    response = self.client.post(
                        self.token_url,
                        {
                            'signed_request': 'test-signed-request',
                            'access_token': 'test-token'
                        }
                    )
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch(
        'social.apps.django_app.utils.BACKENDS',
        ['bluebottle.social.backends.NoStateFacebookOAuth2']
    )
    @mock.patch(
        'bluebottle.social.backends.NoStateFacebookOAuth2.load_signed_request',
        load_signed_request_mock
    )
    def test_token_no_data(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_me_mock):
                    response = self.client.post(self.token_url,
                                                token=self.user_token)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
