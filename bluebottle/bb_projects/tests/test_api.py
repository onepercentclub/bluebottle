from datetime import datetime
import json
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone

from rest_framework import status

from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, ESTestCase

from ..models import ProjectPhase, ProjectTheme


class ProjectEndpointTestCase(BluebottleTestCase):
    """
    Base class for ``projects`` app API endpoints test cases.

    Sets up a common set of three ``Project``s and three ``ProjectTheme``s,
    as well as a dummy testing user which can be used for unit tests.
    """
    def setUp(self):
        super(ProjectEndpointTestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.init_projects()

        self.phase_1 = ProjectPhase.objects.get(slug='plan-new')
        self.phase_2 = ProjectPhase.objects.get(slug='plan-submitted')
        self.phase_3 = ProjectPhase.objects.get(slug='campaign')

        self.theme_1 = ProjectTheme.objects.get(name='Education')
        self.theme_2 = ProjectTheme.objects.get(name='Climate')
        self.theme_3 = ProjectTheme.objects.get(name='Health')

        self.project_1 = ProjectFactory.create(owner=self.user, status=self.phase_1, theme=self.theme_1)
        self.project_2 = ProjectFactory.create(owner=self.user, status=self.phase_2, theme=self.theme_2)
        self.project_3 = ProjectFactory.create(owner=self.user, status=self.phase_3, theme=self.theme_3)


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

        data = response.data['results']

        available_phases = ProjectPhase.objects.all()

        self.assertEqual(len(data), len(available_phases),
                         "Failed to load all the available phases")

        for item in data:
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

        data = response.data['results']

        # Check that it is returning our 1 viewable factory-model project.
        self.assertEqual(len(data), 1)

        # Check sanity on the JSON response.
        for item in data:
            self.assertIn('created', item)
            self.assertIn('description', item)
            self.assertIn('id', item)
            self.assertIn('image', item)
            self.assertIn('owner', item)
            self.assertIn('status', item)

            # Ensure that non-viewable status are filtered out
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

        data = response.data['results']

        # We created 3 projects, but none are viewable with the updated to phase_3...
        self.assertEqual(len(data), 0)


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
        self.assertIn('owner', data)
        self.assertIn('status', data)


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

        self.assertEqual(len(data), 17)

        for item in data:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)

    def test_api_project_theme_list_endpoint_disabled(self):
        """
        Test the API endpoint for Project theme list. Verify that disabled
        themes are not returned
        """
        all_themes = list(ProjectTheme.objects.all())
        disabled = all_themes[0]
        disabled.disabled = True
        disabled.save()

        response = self.client.get(reverse('project_theme_list'))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data), 16)

        for item in data:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertNotEquals(item['id'], disabled.id)


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
            reverse('project_theme_detail', kwargs={'pk': self.project_1.theme.pk}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('description', data)


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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], 'Authentication credentials were not provided.')

    def test_api_manage_project_list_endpoint_success(self):
        """
        Test successful request for a logged in user over the API endpoint for
        manage Project list.
        """
        response = self.client.get(reverse('project_manage_list'), token=self.user_token)

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
            self.assertIn('description', item)
            self.assertIn('country', item)
            self.assertIn('editable', item)

    def test_api_manage_project_list_endpoint_post(self):
        """
        Test successful POST request over the API endpoint for manage Project
        list.
        """
        post_data = {
            'slug': 'test-project',
            'title': 'Testing Project POST request',
            'pitch': 'A new project to be used in unit tests',
            'theme': self.theme_1.pk,
            'status': self.phase_1.pk
        }

        response = self.client.post(reverse('project_manage_list'),
                                    post_data,
                                    token=self.user_token)

        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('created', data)
        self.assertIn('title', data)
        self.assertIn('url', data)
        self.assertIn('status', data)
        self.assertIn('image', data)
        self.assertIn('pitch', data)
        self.assertIn('description', data)
        self.assertIn('country', data)
        self.assertIn('editable', data)

    def test_none_accepted_for_project_amount_asked(self):
        """
        Check that None is allowed for amount_asked, but it will convert it to 0.
        """
        post_data = {
            'slug': 'test-project',
            'title': 'Testing Project POST request',
            'pitch': 'A new project to be used in unit tests',
            'amount_asked': None
        }
        response = self.client.post(reverse('project_manage_list'), post_data, token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['amount_asked'], {'currency': 'EUR', 'amount': Decimal('0')})


class ManageProjectListRoleTests(BluebottleTestCase):
    """ Tests roles on manage project list results """

    def setUp(self):
        super(ManageProjectListRoleTests, self).setUp()

        self.init_projects()

        campaign = ProjectPhase.objects.get(slug='campaign')

        self.other_user = BlueBottleUserFactory.create()
        self.other_token = "JWT {0}".format(self.other_user.get_jwt_token())

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.project1 = ProjectFactory.create(owner=self.some_user,
                                              status=campaign)

        self.project2 = ProjectFactory.create(owner=self.some_user,
                                              task_manager=self.other_user,
                                              status=campaign)

        self.project3 = ProjectFactory.create(owner=self.another_user,
                                              task_manager=self.another_user,
                                              promoter=self.other_user,
                                              status=campaign)

    def test_project_manage_list(self):
        # `some_user` can see two projects:
        # 1) project1 and project2 because she is the owner of the projects
        response = self.client.get(reverse('project_manage_list'), token=self.some_token)
        self.assertEqual(len(response.data['results']), 2)

        # `another_user` can see one project:
        # 1) project3 because he is the task_manager
        response = self.client.get(reverse('project_manage_list'), token=self.another_token)
        self.assertEqual(len(response.data['results']), 1)

        # `other_user` can see two projects:
        # 1) project2 because he is the task_manager
        # 2) project3 because he is the promoter
        response = self.client.get(reverse('project_manage_list'), token=self.other_token)
        self.assertEqual(len(response.data['results']), 2)


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

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
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
        token = "JWT {0}".format(user.get_jwt_token())

        response = self.client.get(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}),
            token=token)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(
            data['detail'], 'You do not have permission to perform this action.')

    def test_api_manage_project_detail_endpoint_success(self):
        """
        Test successful request for a logged in user over the API endpoint for
        manage Project detail.
        """
        response = self.client.get(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}),
            token=self.user_token)

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('created', data)
        self.assertIn('title', data)
        self.assertIn('url', data)
        self.assertIn('status', data)
        self.assertIn('image', data)
        self.assertIn('pitch', data)
        self.assertIn('description', data)
        self.assertIn('country', data)
        self.assertIn('editable', data)
        self.assertIn('project_type', data)

    def test_api_manage_project_detail_check_not_editable(self):
        """
        Test successful request for a logged in user over the API endpoint for
        manage Project detail.
        """
        self.project_1.set_status('campaign')

        response = self.client.put(
            reverse('project_manage_detail', kwargs={'slug': self.project_1.slug}),
            token=self.user_token, data={'title': 'test-new'})

        self.assertEqual(response.status_code, 403)
        self.assertTrue('permission' in response.content)


class TestTinyProjectList(ESTestCase):
    """
    Test case for the ``TinyProjectList`` API view.
    """
    def setUp(self):
        self.init_projects()
        campaign = ProjectPhase.objects.get(slug='campaign')
        new = ProjectPhase.objects.get(slug='plan-new')
        incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        complete = ProjectPhase.objects.get(slug='done-complete')

        self.project1 = ProjectFactory(status=complete)
        self.project1.created = datetime(2017, 03, 18, tzinfo=get_current_timezone())
        self.project1.save()
        self.project2 = ProjectFactory(status=campaign)
        self.project2.created = datetime(2017, 03, 12, tzinfo=get_current_timezone())
        self.project2.save()
        self.project3 = ProjectFactory(status=incomplete)
        self.project3.created = datetime(2017, 03, 01, tzinfo=get_current_timezone())
        self.project3.save()
        self.project4 = ProjectFactory(status=campaign)
        self.project4.created = datetime(2017, 03, 20, tzinfo=get_current_timezone())
        self.project4.save()
        self.project5 = ProjectFactory(status=new)
        self.project5.created = datetime(2017, 03, 20, tzinfo=get_current_timezone())
        self.project5.save()


    def test_tiny_project_list(self):
        response = self.client.get(reverse('project_tiny_preview_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(len(data), 4)

        self.assertEqual(int(data['results'][0]['id']), self.project3.id)
        self.assertEqual(int(data['results'][1]['id']), self.project2.id)
        self.assertEqual(int(data['results'][2]['id']), self.project1.id)
        self.assertEqual(int(data['results'][3]['id']), self.project4.id)
