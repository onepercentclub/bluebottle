from mock import patch

from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.auth.middleware import authorization_logger


class UserTokenTestCase(BluebottleTestCase):
    def setUp(self):
        super(UserTokenTestCase, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

    def user_last_seen(self):
        self.client.get(reverse('user-current'), token=self.user_token)
        self.user.refresh_from_db()
        return self.user.last_seen

    def test_authenticate_user(self):
        """
        Test that we get a token from API when using credentials.
        """
        response = self.client.post(
            reverse("token-auth"),
            data={'email': self.user.email, 'password': 'testing'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'token')

    @patch('bluebottle.auth.middleware.LAST_SEEN_DELTA', 0.000001)
    def test_last_seen(self):
        self.assertEqual(self.user.last_seen, None)

        seen1 = self.user_last_seen()
        self.assertNotEqual(seen1, None)

        seen2 = self.user_last_seen()
        self.assertNotEqual(seen2, None)
        self.assertTrue(seen2 > seen1)

    @patch('bluebottle.auth.middleware.LAST_SEEN_DELTA', 10)
    def test_last_seen_delta(self):
        seen1 = self.user_last_seen()
        seen2 = self.user_last_seen()
        self.assertNotEqual(seen1, None)
        self.assertNotEqual(seen2, None)
        self.assertTrue(seen1 == seen2)

    def test_login_failure_is_logged(self):
        with patch.object(authorization_logger, 'error') as error:
            response = self.client.post(
                reverse("token-auth"),
                data={'email': self.user.email, 'password': 'wrong'}
            )
            self.assertEqual(response.status_code, 400)

            self.assertTrue(
                'Authorization failed: {} 127.0.0.1'.format(self.user.email) in error.call_args[0]
            )

    def test_login_failure_form_data_is_logged(self):
        with patch.object(authorization_logger, 'error') as error:
            response = self.client.post(
                reverse("token-auth"),
                {'email': self.user.email, 'password': 'wrong'},
                format='multipart'
            )
            self.assertEqual(response.status_code, 400)

            self.assertTrue(
                'Authorization failed: {} 127.0.0.1'.format(self.user.email) in error.call_args[0]
            )
