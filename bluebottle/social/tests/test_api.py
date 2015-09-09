import json

import mock
from django.core.urlresolvers import reverse

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class SocialTokenAPITestCase(BluebottleTestCase):
    """
    Test the social authorization token api endpoint
    """
    def setUp(self):
        super(SocialTokenAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.token_url = reverse('access-token', kwargs={'backend': 'facebook'})

    def test_vote(self):
        with mock.patch('social.apps.django_app.utils.BACKENDS', ['social.backends.facebook.FacebookOAuth2']):
            response = self.client.post(self.token_url,
                                        {'code': 'test-code', 'state': 'test-state'},
                                        token=self.user_token)
            self.assertEqual(response.status_code, 201)


