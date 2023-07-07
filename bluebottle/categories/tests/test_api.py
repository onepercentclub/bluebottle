import json

from django.urls import reverse
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
        category_details = {
            'title': 'Nice things',
            'description': 'Chit chat blah blah'
        }

        cat = CategoryFactory.create(**category_details)
        cat.set_current_language('nl')
        cat.title = 'Leuke dingen'
        cat.save()

        category_details = {
            'title': 'Other things',
            'description': 'Chit chat blah blah'
        }

        cat = CategoryFactory.create(**category_details)
        cat.set_current_language('nl')
        cat.title = 'Andere dingen'
        cat.save()

        url = reverse('category-list')

        response = self.client.get(url, HTTP_X_APPLICATION_LANGUAGE='en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['data'][0]['attributes']['title'], 'Nice things')
        self.assertEqual(data['data'][1]['attributes']['title'], 'Other things')

        # Confirm that we can retrieve Dutch titles too.
        response = self.client.get(url, HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data['data']), 2)

        self.assertEqual(data['data'][0]['attributes']['title'], 'Andere dingen')
        self.assertEqual(data['data'][1]['attributes']['title'], 'Leuke dingen')

    def test_category_content(self):
        category_details = {
            'title': 'Nice things',
            'description': 'Chit chat blah blah'
        }

        category = CategoryFactory.create(**category_details)

        category_content = {
            'title': 'category content title',
            'description': 'category content description',
            'link_text': 'Find out more...',
            'link_url': 'http://link.com',
            'category': category
        }

        CategoryContentFactory.create(**category_content)

        url = reverse('category-detail', kwargs={'pk': category.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)['data']['attributes']
        self.assertEqual(data['contents'][0]['title'], 'category content title')
        self.assertEqual(data['contents'][0]['description'], 'category content description')
        self.assertEqual(data['contents'][0]['link_text'], 'Find out more...')
        self.assertEqual(data['contents'][0]['link_url'], 'http://link.com')
        self.assertTrue(
            all(
                field in ('title', 'description', 'image', 'link_text', 'link_url', 'sequence')
                for field in list(data['contents'][0].keys())
            )
        )
