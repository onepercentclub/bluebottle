from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class UserTokenTestCase(BluebottleTestCase):
    def setUp(self):
        super(UserTokenTestCase, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()

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
