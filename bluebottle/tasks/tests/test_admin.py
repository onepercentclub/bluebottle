from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.utils.timezone import now

from bluebottle.tasks.models import Task
from bluebottle.tasks.admin import TaskAdmin, DeadlineToAppliedFilter
from bluebottle.test.factory_models.tasks import TaskFactory
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
        self.task_admin = TaskAdmin(Task, self.site)

    def test_list_filter_task_skills(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertIn('deadline', self.task_admin.get_list_filter(request))
        self.assertIn(DeadlineToAppliedFilter, self.task_admin.get_list_filter(request))


class TestDeadlineToApplyFilter(BluebottleTestCase):
    def setUp(self):
        super(TestDeadlineToApplyFilter, self).setUp()
        self.init_projects()
        self.request = RequestFactory().get('/')
        self.site = AdminSite()
        self.task_admin = TaskAdmin(Task, self.site)

        for days in [-5, 3, 10]:
            TaskFactory.create(deadline_to_apply=now() + timedelta(days=days))

    def test_deadline_to_apply_filter_deadline_passed(self):
        filter = DeadlineToAppliedFilter(None, {'deadline_to_apply': 0}, Task, self.task_admin)
        queryset = filter.queryset(self.request, Task.objects.all())
        self.assertEqual(len(queryset), 1)

    def test_deadline_to_apply_filter_7_days(self):
        filter = DeadlineToAppliedFilter(None, {'deadline_to_apply': 7}, Task, self.task_admin)
        queryset = filter.queryset(self.request, Task.objects.all())
        self.assertEqual(len(queryset), 1)

    def test_deadline_to_apply_filter_30_days(self):
        filter = DeadlineToAppliedFilter(None, {'deadline_to_apply': 30}, Task, self.task_admin)
        queryset = filter.queryset(self.request, Task.objects.all())
        self.assertEqual(len(queryset), 2)

    def test_deadline_to_apply_filter_not_set(self):
        filter = DeadlineToAppliedFilter(None, {}, Task, self.task_admin)
        queryset = filter.queryset(self.request, Task.objects.all())
        self.assertEqual(len(queryset), 3)
