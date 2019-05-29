from django.urls import reverse

from rest_framework import status
from bluebottle.events.tests.factories import EventFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class ActivityTestCase(BluebottleTestCase):

    def setUp(self):
        super(ActivityTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('activity-list')
        self.user = BlueBottleUserFactory()

    def test_list_activities(self):
        EventFactory.create_batch(4)
        response = self.client.get(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 4)
