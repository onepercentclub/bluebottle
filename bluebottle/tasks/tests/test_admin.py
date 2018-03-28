from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls.base import reverse

from bluebottle.tasks.models import Task, Skill
from bluebottle.tasks.admin import TaskAdmin, DeadlineToApplyFilter, DeadlineFilter, SkillAdmin
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import TaskFactory, SkillFactory
from bluebottle.test.utils import BluebottleTestCase, BluebottleAdminTestCase

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

        self.assertIn(DeadlineFilter, self.task_admin.get_list_filter(request))
        self.assertIn(DeadlineToApplyFilter, self.task_admin.get_list_filter(request))

    def test_fields_appear(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        for field in ['title', 'description', 'skill', 'time_needed', 'status',
                      'date_status_change', 'people_needed', 'project', 'author',
                      'type', 'accepting', 'location', 'deadline', 'deadline_to_apply']:
            self.assertIn(field, self.task_admin.get_fields(request))


class TestSkillAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestSkillAdmin, self).setUp()
        self.init_projects()
        self.client.force_login(self.superuser)
        self.request_factory = RequestFactory()
        self.site = AdminSite()
        self.skill_admin = SkillAdmin(Skill, self.site)

    def test_fields_appear(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        for field in ['member_link', 'task_link']:
            self.assertIn(field, self.skill_admin.get_fields(request))

        skill = SkillFactory.create()
        members = BlueBottleUserFactory.create_batch(3)
        for member in members:
            member.skills = [skill]
            member.save()

        TaskFactory.create_batch(2, skill=skill)

        skill_url = reverse('admin:tasks_skill_change', args=(skill.id, ))
        response = self.client.get(skill_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '3 users')
        self.assertContains(response, '2 tasks')
