import json

from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.utils import BluebottleTestCase


class CategoriesTestCase(BluebottleTestCase):
    """
    Integration tests for the Categories API.
    """

    def setUp(self):
        super(CategoriesTestCase, self).setUp()
        self.init_projects()

    def test_partner_project(self):
        cat = {
            'title': 'Nice things',
            'description': 'Chit chat blah blah'
        }

        CategoryFactory.create(**cat)

        url = reverse('category-list')

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]['title'], cat['title'])

        # Confirm that we can restrieve dutch titles too.
        response = self.client.get(url, {'language': 'nl'})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]['title'], cat['title'])
