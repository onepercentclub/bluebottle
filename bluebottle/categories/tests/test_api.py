import json

from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.factory_models.categories import CategoryFactory, CategoryContentFactory
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

    def test_category_content(self):
        category_details = {
            'title': 'Nice things',
            'description': 'Chit chat blah blah'
        }

        category = CategoryFactory.create(**category_details)

        category_content = {
            'title': 'category content title',
            'description': 'category content description',
            'video_url': 'http://vimeo.com',
            'link': 'http://link.com',
            'category': category
        }

        CategoryContentFactory.create(**category_content)

        url = reverse('category-detail', kwargs={'slug': category.slug})

        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEquals(data['contents'][0]['title'], 'category content title')
        self.assertEquals(data['contents'][0]['description'], 'category content description')
        self.assertEquals(data['contents'][0]['video_url'], 'http://vimeo.com')
        self.assertEquals(data['contents'][0]['link'], 'http://link.com')
        self.assertTrue(all(field in ('title', 'description', 'image', 'video_url', 'link')
                            for field in data['contents'][0].keys()
                            )
                        )
