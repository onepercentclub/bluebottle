from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory

from bluebottle.projects.models import Project
from bluebottle.tasks.admin import TaskAdmin
from bluebottle.test.utils import BluebottleTestCase


factory = RequestFactory()


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None):
        self.perms = perms or []

    def has_perm(self, perm):
        return perm in self.perms


class TestTaskAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestTaskAdmin, self).setUp()
        self.init_projects()
        self.request_factory = RequestFactory()
        self.site = AdminSite()
        self.task_admin = TaskAdmin(Project, self.site)

    def test_list_filter_task_skills(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertIn('deadline', self.task_admin.get_list_filter(request))
        self.assertIn('deadline_to_apply', self.task_admin.get_list_filter(request))
