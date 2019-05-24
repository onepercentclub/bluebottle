from django.urls import reverse

from rest_framework import status
from bluebottle.events.tests.factories import EventFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class ActivityTestCase(BluebottleTestCase):

    def setUp(self):
        self.url = reverse('activity-list')
        self.user = BlueBottleUserFactory()
        self.token = "JWT {0}".format(self.user.get_jwt_token())

    def test_list_activities(self):
        EventFactory.create_batch(4)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 4)
