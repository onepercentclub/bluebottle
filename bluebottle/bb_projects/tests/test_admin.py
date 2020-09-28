# -*- coding: utf-8 -*-
from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from rest_framework.status import HTTP_200_OK

from bluebottle.bb_projects.admin import ProjectThemeAdmin
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.tasks.models import Skill
from bluebottle.test.utils import BluebottleAdminTestCase


class TestThemeAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestThemeAdmin, self).setUp()
        self.site = AdminSite()
        self.skill_admin = ProjectThemeAdmin(Skill, self.site)
        self.client.force_login(self.superuser)
        InitiativeFactory.create()

    def test_theme_admin_list(self):
        url = reverse('admin:bb_projects_projecttheme_changelist')
        response = self.client.get(url)
        self.assertTrue(response, HTTP_200_OK)
