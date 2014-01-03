import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.projects import (
    ProjectFactory, ProjectThemeFactory, ProjectDetailFieldFactory)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class ProjectEndpointTestCase(TestCase):
    """
    Base class for ``projects`` app API endpoints test cases.

    Sets up a common set of three ``Project``s and three ``ProjectTheme``s,
    as well as a dummy testing user which can be used for unit tests.
    """
    def setUp(self):
        self.user = BlueBottleUserFactory.create()

        self.project_1 = ProjectFactory.create(owner=self.user)
        self.project_2 = ProjectFactory.create(owner=self.user)
        self.project_3 = ProjectFactory.create(owner=self.user)

        self.theme_1 = ProjectThemeFactory.create()
        self.theme_2 = ProjectThemeFactory.create()
        self.theme_3 = ProjectThemeFactory.create()

        self.detail_field_1 = ProjectDetailFieldFactory.create()
        self.detail_field_2 = ProjectDetailFieldFactory.create()
        self.detail_field_3 = ProjectDetailFieldFactory.create()


class TestProjectList(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectList`` API view.

    Endpoint: /api/projects/projects/
    """
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


class TestProjectDetail(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectDetail`` API view.

    Endpoint: /api/projects/projects/{slug}
    """
    def test_api_project_detail_endpoint(self):
        """
        Test the API endpoint for Project detail.
        """
        response = self.client.get(
            reverse('project_detail', kwargs={'slug': self.project_1.slug}))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('created', data)
        self.assertIn('description', data)
        self.assertIn('details', data)
        self.assertIn('id', data)
        self.assertIn('image', data)
        self.assertIn('meta_data', data)
        self.assertIn('owner', data)
        self.assertIn('phase', data)


class TestProjectPreviewList(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectPreviewList`` API view.

    Endpoint: /api/projects/previews
    """
    def test_api_project_preview_list_endpoint(self):
        """
        Test the API endpoint for Project preview list.
        """
        response = self.client.get(reverse('project_preview_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(data['count'], 3)

        for item in data['results']:
            self.assertIn('id', item)
            self.assertIn('title', item)
            self.assertIn('image', item)
            self.assertIn('phase', item)
            self.assertIn('country', item)


class TestProjectPreviewDetail(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectPreviewDetail`` API view.

    Endpoint: /api/projects/preview/{slug}
    """
    def test_api_project_preview_detail_endpoint(self):
        """
        Test the API endpoint for Project preview detail.
        """
        response = self.client.get(
            reverse('project_preview_detail',
                    kwargs={'slug': self.project_1.slug}))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('image', data)
        self.assertIn('phase', data)
        self.assertIn('country', data)


class TestProjectThemeList(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectThemeList`` API view.

    Endpoint: /api/projects/themes
    """
    def test_api_project_theme_list_endpoint(self):
        """
        Test the API endpoint for Project theme list.
        """
        response = self.client.get(reverse('project_theme_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(data['count'], 3)

        for item in data['results']:
            self.assertIn('id', item)
            self.assertIn('title', item)


class TestProjectThemeDetail(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectThemeDetail`` API view.

    Endpoint: /api/projects/themes/{pk}
    """
    def test_api_project_theme_detail_endpoint(self):
        """
        Test the API endpoint for Project theme detail.
        """
        response = self.client.get(
            reverse('project_theme_detail', kwargs={'pk': self.project_1.pk}))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertIn('id', data)
        self.assertIn('title', data)


class TestProjectDetailFieldList(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectDetailFieldList`` API view.

    Endpoint: /api/projects/fields
    """
    def test_api_project_detail_field_list_endpoint(self):
        """
        Test the API endpoint for Project detail field list.
        """
        response = self.client.get(reverse('project_detail_field_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        for item in data:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertIn('type', item)
            self.assertIn('options', item)
            self.assertIn('attributes', item)
