import json

from django.test import TestCase
from django.core.urlresolvers import reverse

#from bluebottle.bb_projects.models import ProjectBudgetLine
from bluebottle.test.factory_models.projects import (
    #ProjectDetailFieldFactory, ProjectBudgetLineFactory,
    ProjectFactory, ProjectThemeFactory,
    ProjectPhaseFactory)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from ..models import ProjectPhase


class ProjectEndpointTestCase(TestCase):
    """
    Base class for ``projects`` app API endpoints test cases.

    Sets up a common set of three ``Project``s and three ``ProjectTheme``s,
    as well as a dummy testing user which can be used for unit tests.
    """
    def setUp(self):
        self.user = BlueBottleUserFactory.create()

        self.phase_1 = ProjectPhaseFactory.create()
        self.phase_2 = ProjectPhaseFactory.create()
        self.phase_3 = ProjectPhaseFactory.create()

        self.theme_1 = ProjectThemeFactory.create()
        self.theme_2 = ProjectThemeFactory.create()
        self.theme_3 = ProjectThemeFactory.create()

        self.project_1 = ProjectFactory.create(
            owner=self.user, status=self.phase_1, theme=self.theme_1)
        self.project_2 = ProjectFactory.create(
            owner=self.user, status=self.phase_2, theme=self.theme_2)
        self.project_3 = ProjectFactory.create(
            owner=self.user, status=self.phase_3, theme=self.theme_3)

        # self.detail_field_1 = ProjectDetailFieldFactory.create()
        # self.detail_field_2 = ProjectDetailFieldFactory.create()
        # self.detail_field_3 = ProjectDetailFieldFactory.create()


class TestProjectPhaseList(ProjectEndpointTestCase):
    """
    Test case for the ``ProjectPhase`` API view. Returns all the Phases
    that can be assigned to a project.

    Endpoint: /api/projects/phases/
    """
    def test_api_phases_list_endpoint(self):
        """
        Tests that the list of project phases can be obtained from its
        endpoint.
        """
        
        response = self.client.get(reverse('project_phase_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        available_phases = ProjectPhase.objects.all()

        self.assertEqual(data['count'], len(available_phases),
                         "Failed to load all the available phases")

        for item in data['results']:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertIn('sequence', item)
            self.assertIn('active', item)
            self.assertIn('editable', item)
            self.assertIn('viewable', item)
    

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

        # Check that it is returning our 3 viewable factory-model projects.
        self.assertEqual(data['count'], 3)

        # Check sanity on the JSON response.
        for item in data['results']:
            self.assertIn('created', item)
            self.assertIn('description', item)
            self.assertIn('id', item)
            self.assertIn('image', item)
            self.assertIn('meta_data', item)
            self.assertIn('owner', item)
            self.assertIn('status', item)
            
            #Ensure that non-viewable status are filtered out
            phase = ProjectPhase.objects.get(id=item['status'])
            self.assertTrue(phase.viewable, "Projects with non-viewable status were returned")

    def test_api_project_list_endpoint_status_viewable(self):
        """
        Test that the non-viewable projects are not returned by the API.
        """
        self.phase_3.viewable = False
        self.phase_3.save()

        # So, now our ``self.project_3`` should be non-viewable...
        response = self.client.get(reverse('project_list'))

        data = json.loads(response.content)
        # We created 3 projects, but one is non viewable...
        self.assertEqual(data['count'], 2)


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
        self.assertIn('id', data)
        self.assertIn('image', data)
        self.assertIn('meta_data', data)
        self.assertIn('owner', data)
        self.assertIn('status', data)


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
            self.assertIn('status', item)
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
        self.assertIn('status', data)
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
            self.assertIn('name', item)


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
        self.assertIn('name', data)


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


class TestManageProjectList(ProjectEndpointTestCase):
    """
    Test case for the ``ManageProjectList`` API view.

    Endpoint: /api/projects/manage
    """
    def test_api_manage_project_list_endpoint_login_required(self):
        """
        Test login required for the API endpoint for manage Project list.
        """
        response = self.client.get(reverse('project_manage_list'))

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(
            data['detail'], 'Authentication credentials were not provided.')

    def test_api_manage_project_list_endpoint_success(self):
        """
        Test successful request for a logged in user over the API endpoint for
        manage Project list.
        """
        self.client.login(email=self.user.email, password='testing')
        response = self.client.get(reverse('project_manage_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 3)

        for item in data['results']:
            self.assertIn('id', item)
            self.assertIn('created', item)
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertIn('status', item)
            self.assertIn('image', item)
            self.assertIn('pitch', item)
            self.assertIn('tags', item)
            self.assertIn('description', item)
            self.assertIn('country', item)
            self.assertIn('latitude', item)
            self.assertIn('longitude', item)
            self.assertIn('reach', item)
            self.assertIn('organization', item)
            self.assertIn('video_html', item)
            self.assertIn('video_url', item)
            self.assertIn('editable', item)

    def test_api_manage_project_list_endpoint_post(self):
        """
        Test successful POST request over the API endpoint for manage Project
        list.
        """
        post_data = {
            'title': 'Testing Project POST request',
            'pitch': 'A new project to be used in unit tests',
            'theme': self.theme_1.pk,
            'status': self.phase_1.pk
        }

        self.client.login(email=self.user.email, password='testing')
        response = self.client.post(reverse('project_manage_list'), post_data)

        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('created', data)
        self.assertIn('title', data)
        self.assertIn('url', data)
        self.assertIn('status', data)
        self.assertIn('image', data)
        self.assertIn('pitch', data)
        self.assertIn('tags', data)
        self.assertIn('description', data)
        self.assertIn('country', data)
        self.assertIn('latitude', data)
        self.assertIn('longitude', data)
        self.assertIn('reach', data)
        self.assertIn('organization', data)
        self.assertIn('video_html', data)
        self.assertIn('video_url', data)
        self.assertIn('editable', data)


class TestManageProjectDetail(ProjectEndpointTestCase):
    """
    Test case for the ``ManageProjectDetail`` API view.

    Endpoint: /api/projects/manage/{slug}
    """
    def test_api_manage_project_detail_endpoint_login_required(self):
        """
        Test login required for the API endpoint for manage Project detail.
        """
        response = self.client.get(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}))

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(
            data['detail'], 'Authentication credentials were not provided.')

    def test_api_manage_project_detail_endpoint_not_owner(self):
        """
        Test unauthorized request made by a user who is not the owner of the
        Project over the API endpoint for manage Project detail.
        """
        user = BlueBottleUserFactory.create(
            email='jane.doe@onepercentclub.com',
            username='janedoe'
        )

        self.client.login(email=user.email, password='testing')
        response = self.client.get(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}))

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(
            data['detail'], 'You do not have permission to perform this action.')

    def test_api_manage_project_detail_endpoint_success(self):
        """
        Test successful request for a logged in user over the API endpoint for
        manage Project detail.
        """
        self.client.login(email=self.user.email, password='testing')
        response = self.client.get(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('created', data)
        self.assertIn('title', data)
        self.assertIn('url', data)
        self.assertIn('status', data)
        self.assertIn('image', data)
        self.assertIn('pitch', data)
        self.assertIn('tags', data)
        self.assertIn('description', data)
        self.assertIn('country', data)
        self.assertIn('latitude', data)
        self.assertIn('longitude', data)
        self.assertIn('reach', data)
        self.assertIn('organization', data)
        self.assertIn('video_html', data)
        self.assertIn('video_url', data)
        self.assertIn('editable', data)


class TestManageProjectBudgetLineList(ProjectEndpointTestCase):
    """
    Test case for the ``ManageProjectBudgetLineList`` API view.

    Endpoint: /api/projects/budgetlines/manage
    """
    def setUp(self):
        super(TestManageProjectBudgetLineList, self).setUp()

        self.project_budget_1 = ProjectBudgetLineFactory.create(
            project=self.project_1)
        self.project_budget_2 = ProjectBudgetLineFactory.create(
            project=self.project_2)
        self.project_budget_3 = ProjectBudgetLineFactory.create(
            project=self.project_3)

    def test_api_manage_project_budgetline_list_endpoint(self):
        """
        Test API endpoint for manage Project budgetline list.
        """
        response = self.client.get(reverse('project_budgetline_manage_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 3)

        for item in data['results']:
            self.assertIn('id', item)
            self.assertIn('project', item)
            self.assertIn('description', item)
            self.assertIn('amount', item)

    def test_api_manage_project_budgetline_list_post_authentication(self):
        """
        Test POST request over API requires authentication.
        """
        post_data = {
            'project': self.project_1.slug,
            'description': 'The testing project.',
            # We set the amount in Euros in the POST request.
            'amount': 1000
        }
        response = self.client.post(
            reverse('project_budgetline_manage_list'), post_data)

        self.assertEqual(response.status_code, 403)

    def test_api_manage_project_budgetline_list_post(self):
        """
        Test successful POST request over API endpoint for manage Project
        budgetline.
        """
        post_data = {
            'project': self.project_1.slug,
            'description': 'The testing project.',
            # We set the amount in Euros in the POST request.
            'amount': 1000
        }
        self.client.login(email=self.project_1.owner.email, password='testing')
        response = self.client.post(
            reverse('project_budgetline_manage_list'), post_data)

        self.assertEqual(response.status_code, 201)

        budgetline = ProjectBudgetLine.objects.latest('pk')

        self.assertEqual(budgetline.description, post_data['description'])
        self.assertEqual(budgetline.project.slug, post_data['project'])
        # In the model, the amount is stored in Euro-cents.
        self.assertEqual(budgetline.amount, 100000)


class TestManageProjectsBudgetLineDetail(ProjectEndpointTestCase):
    """
    Test case for the ``ManageProjectBudgetLineDetail`` API view.

    Endpoint: /api/projects/budgetlines/manage/{pk}
    """
    def setUp(self):
        super(TestManageProjectsBudgetLineDetail, self).setUp()

        self.project_budget_1 = ProjectBudgetLineFactory.create(
            project=self.project_1)
        self.project_budget_2 = ProjectBudgetLineFactory.create(
            project=self.project_2)
        self.project_budget_3 = ProjectBudgetLineFactory.create(
            project=self.project_3)

        self.put_data = {
            'project': self.project_budget_1.project.slug,
            'description': 'Modified description for testing',
            'amount': 2000
        }

    def test_api_manage_project_budgetline_detail(self):
        """
        Test API endpoint for manage Project budgetline detail.
        """
        response = self.client.get(
            reverse('project_budgetline_manage_detail',
                    kwargs={'pk': self.project_budget_1.pk}))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('project', data)
        self.assertIn('description', data)
        self.assertIn('amount', data)

    def test_api_manage_project_budgetline_detail_put_authentication(self):
        """
        Test PUT method needs the user to be authenticated.
        """
        json_data = json.dumps(self.put_data)

        response = self.client.put(
            reverse('project_budgetline_manage_detail',
                    kwargs={'pk': self.project_budget_1.pk}),
            json_data, content_type='application/json')

        self.assertEqual(response.status_code, 403)

    def test_api_manage_project_budgetline_detail_put(self):
        """
        Test successful PUT method over manage Project budgetline detail
        endpoint.
        """
        json_data = json.dumps(self.put_data)

        self.client.login(email=self.project_1.owner.email, password='testing')
        response = self.client.put(
            reverse('project_budgetline_manage_detail',
                    kwargs={'pk': self.project_budget_1.pk}),
            json_data, content_type='application/json', follow=True)

        self.assertEqual(response.status_code, 200)

        budgetline = ProjectBudgetLine.objects.get(pk=self.project_budget_1.pk)
        self.assertEqual(budgetline.amount, 200000)
        self.assertEqual(budgetline.description, self.put_data['description'])
        self.assertEqual(budgetline.project.slug, self.put_data['project'])

    def test_api_manage_project_budgetline_detail_delete_authentication(self):
        """
        Test DELETE method needs the user to be authenticated.
        """
        response = self.client.delete(
            reverse('project_budgetline_manage_detail',
                    kwargs={'pk': self.project_budget_1.pk}),
            content_type='application/json')

        self.assertEqual(response.status_code, 403)

    def test_api_manage_project_budgetline_detail_delete(self):
        """
        Test DELETE method over manage Project budgetline detail endpoint.
        """
        self.client.login(email=self.project_1.owner.email, password='testing')
        response = self.client.delete(
            reverse('project_budgetline_manage_detail',
                    kwargs={'pk': self.project_budget_1.pk}),
            content_type='application/json', follow=True)

        self.assertEqual(response.status_code, 204)

        self.assertRaises(
            ProjectBudgetLine.DoesNotExist,
            ProjectBudgetLine.objects.get,
            pk=self.project_budget_1.pk)
