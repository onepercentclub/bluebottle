# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from rest_framework.status import HTTP_200_OK

from bluebottle.assignments.tests.factories import AssignmentFactory
from bluebottle.tasks.admin import SkillAdmin
from bluebottle.tasks.models import Skill
from bluebottle.test.utils import BluebottleAdminTestCase


class TestSkillAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestSkillAdmin, self).setUp()
        self.site = AdminSite()
        self.skill_admin = SkillAdmin(Skill, self.site)
        self.client.force_login(self.superuser)
        AssignmentFactory.create()

    def test_skill_admin_list(self):
        url = reverse('admin:tasks_skill_changelist')
        response = self.client.get(url)
        self.assertTrue(response, HTTP_200_OK)
