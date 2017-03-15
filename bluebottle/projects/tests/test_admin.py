import json
import mock

import requests

from django.contrib.admin.sites import AdminSite
from django.contrib import messages
from django.test.client import RequestFactory
from bluebottle.projects.admin import ProjectAdmin
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase, override_settings


PAYOUT_URL = 'http://localhost:8001/payouts/update/'


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None):
        self.perms = perms or []

    def has_perm(self, perm):
        return perm in self.perms


@override_settings(PAYOUT_SERVICE={
    'service': 'dorado',
    'url': PAYOUT_URL
})
class TestProjectAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAdmin, self).setUp()
        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.init_projects()
        self.project_admin = ProjectAdmin(Project, self.site)
        self.mock_response = requests.Response()
        self.mock_response.status_code = 200

    def test_fieldsets(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_fieldsets(request)[0][1]['fields']
        )

    def test_fieldsets_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_fieldsets(request)
        )

    def test_list_filter(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_filter(request)
        )

    def test_list_filter_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_filter(request)
        )

    def test_list_display(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_display(request)
        )

    def test_list_display_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_display(request)
        )

    def test_mark_payout_as_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

    def test_mark_payout_as_approved_validation_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        self.mock_response.status_code = 400
        self.mock_response._content = json.dumps({'errors': {'name': ['This field is required']}})
        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Account details: name, this field is required.', level=messages.ERROR
        )

    def test_mark_payout_as_approved_no_permissions(self):
        request = self.request_factory.post('/')
        request.user = MockUser()

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            project = ProjectFactory.create(payout_status='needs_approval')

        response = self.project_admin.approve_payout(request, project.id)
        self.assertEqual(response.status_code, 403)
        request_mock.assert_not_called()

    def test_mark_payout_as_approved_wrong_status(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='done')
        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'done'
        )
        request_mock.assert_not_called()
        message_mock.assert_called()

    def test_read_only_status_after_payout_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        # Project status should be editable
        self.assertFalse(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )

        with mock.patch('requests.post', return_value=self.mock_response):
            self.project_admin.approve_payout(request, project.id)

        project = Project.objects.get(id=project.id)

        # Project status should be readonly after payout has been approved
        self.assertTrue(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )
