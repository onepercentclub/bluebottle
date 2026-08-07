from django.urls import reverse
from rest_framework import status

from bluebottle.activity_links.tests.factories import LinkedFundingFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class LinkedActivityImageAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(LinkedActivityImageAPITestCase, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.linked = LinkedFundingFactory.create(
            image=ImageFactory.create(),
        )

    def test_linked_activity_image_endpoint(self):
        url = reverse(
            'activity-links:image',
            args=(self.linked.pk, '200x200'),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_linked_activity_image_not_found(self):
        url = reverse('activity-links:image', args=(99999, '200x200'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
