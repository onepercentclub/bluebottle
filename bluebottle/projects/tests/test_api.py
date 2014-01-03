import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class TestProjectList(TestCase):
    """
    Test case for the ``ProjectList`` API view.

    Endpoint: /api/projects/projects/
    """
    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.project_1 = ProjectFactory.create(owner=self.user)
        self.project_2 = ProjectFactory.create(owner=self.user)
        self.project_3 = ProjectFactory.create(owner=self.user)

    def test_api_project_list_endpoint(self):
        """
        Test the API endpoint for Projects list.
        """
        response = self.client.get(reverse('project_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        # Check that it is returning our 3 factory-model projects.
        self.assertEqual(data['count'], 3)

        # Check sanity on the JSON response.
        for item in data['results']:
            self.assertIn('created', item)
            self.assertIn('description', item)
            self.assertIn('details', item)
            self.assertIn('id', item)
            self.assertIn('image', item)
            self.assertIn('meta_data', item)
            self.assertIn('owner', item)
            self.assertIn('phase', item)
