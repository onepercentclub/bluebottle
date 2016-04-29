from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.factory_models.redirect import RedirectFactory
from bluebottle.test.utils import BluebottleTestCase


class RedirectApiTestCase(BluebottleTestCase):

    def setUp(self):
        super(RedirectApiTestCase, self).setUp()
        self.redirect_url = reverse('redirect-list')

    def test_redirect_api(self):

        RedirectFactory.create_batch(5)

        response = self.client.get(self.redirect_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
