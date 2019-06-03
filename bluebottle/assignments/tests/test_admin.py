# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.urls.base import reverse
from rest_framework import status

from bluebottle.assignments.admin import AssignmentAdmin
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.tests.factories import AssignmentFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestAssignmentAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestAssignmentAdmin, self).setUp()
        self.site = AdminSite()
        self.assignment_admin = AssignmentAdmin(Assignment, self.site)
        self.assignment = AssignmentFactory.create(status='created')
        self.assignment_url = reverse('admin:assignments_assignment_change', args=(self.assignment.id,))
        self.assignment.save()

    def test_assignment_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.assignment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
