import json
from urlparse import parse_qs

import mock
import httmock
from django.core.urlresolvers import reverse

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


@httmock.urlmatch(netloc='graph.facebook.com', path='/v2.3/oauth/access_token')
def facebook_access_token_mock(url, request):
    query = parse_qs(url.query)

    if query['code'][0] == 'test-code' and query['client_secret'][0] == 'test-secret':
        return json.dumps({'access_token': '1234'})
    else:
        return {
            'content': json.dumps({'error': 'incorrect code or secret'}),
            'status_code': 400
        }


@httmock.urlmatch(netloc='graph.facebook.com', path='/v2.3/me')
def facebook_me_mock(url, request):
    return json.dumps({'firstname': 'bla', 'lastname': 'bla'})


class SocialTokenAPITestCase(BluebottleTestCase):
    """
    Test the social authorization token api endpoint
    """
    def setUp(self):
        super(SocialTokenAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.token_url = reverse('access-token', kwargs={'backend': 'facebook'})

    def test_token(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-secret'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_access_token_mock, facebook_me_mock):
                    response = self.client.post(self.token_url,
                                                {'code': 'test-code'},
                                                token=self.user_token)
                    self.assertEqual(response.status_code, 201)
                    self.assertEqual(json.loads(response.content), {})

    def test_token_invalid_code(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-secret'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_access_token_mock, facebook_me_mock):
                    response = self.client.post(self.token_url,
                                                {'code': 'test-invalid'},
                                                token=self.user_token)
                    self.assertEqual(response.status_code, 400)

    def test_token_invalid_secret(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_access_token_mock, facebook_me_mock):
                    response = self.client.post(self.token_url,
                                                {'code': 'test-invalid'},
                                                token=self.user_token)
                    self.assertEqual(response.status_code, 400)

    def test_token_unauthenticated(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_access_token_mock, facebook_me_mock):
                    response = self.client.post(self.token_url,
                                                {'code': 'test-invalid'})
                    self.assertEqual(response.status_code, 403)

    def test_token_no_code(self):
        with self.settings(SOCIAL_AUTH_FACEBOOK_SECRET='test-invalid'):
            with mock.patch(
                    'social.apps.django_app.utils.BACKENDS',
                    ['bluebottle.social.backends.NoStateFacebookOAuth2']):
                with httmock.HTTMock(facebook_access_token_mock, facebook_me_mock):
                    response = self.client.post(self.token_url, token=self.user_token)
                    self.assertEqual(response.status_code, 400)
