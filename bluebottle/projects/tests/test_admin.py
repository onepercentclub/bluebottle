from mock import patch

from django.contrib.admin.sites import AdminSite

from bluebottle.projects.admin import ProjectAdmin
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None):
        self.perms = perms or []

    def has_perm(self, perm):
        return perm in self.perms


class TestProjectAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAdmin, self).setUp()
        self.site = AdminSite()

        self.init_projects()
        self.project_admin = ProjectAdmin(Project, self.site)

    def test_fieldsets(self):
        request = MockRequest()
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_fieldsets(request)[0][1]['fields']
        )

    def test_fieldsets_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_fieldsets(request)
        )

    def test_list_filter(self):
        request = MockRequest()
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_filter(request)
        )

    def test_list_filter_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_filter(request)
        )

    def test_list_display(self):
        request = MockRequest()
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

    @patch('bluebottle.payouts_dorado.adapters.requests.post',
           return_value=type('obj', (object,), {'status_code': 200, 'content': '{"status": "success"}'}))
    def test_mark_payout_as_approved(self, mock_post):
        request = MockRequest()
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        self.project_admin.approve_payout(request, project.id)
        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'created'
        )

    def test_mark_payout_as_approved_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        project = ProjectFactory.create(payout_status='needs_approval')

        self.project_admin.approve_payout(request, project.id)
        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'needs_approval'
        )

    def test_mark_payout_as_approved_wrong_status(self):
        request = MockRequest()
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='done')

        self.project_admin.approve_payout(request, project.id)
        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'done'
        )

    @patch('bluebottle.payouts_dorado.adapters.requests.post',
           return_value=type('obj', (object,), {'status_code': 200, 'content': '{"status": "success"}'}))
    def test_read_only_status_after_payout_approved(self, mock_post):
        request = MockRequest()
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        # Project status should be editable
        self.assertFalse(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )

        self.project_admin.approve_payout(request, project.id)

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.payout_status, 'created')

        # Project status should be readonly after payout has been approved
        self.assertTrue(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )
