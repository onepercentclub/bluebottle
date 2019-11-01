from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.template.response import TemplateResponse
from django.http.response import HttpResponseForbidden

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class AdminPermissionsTest(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

        # Create staff user without superuser permission
        self.user = BlueBottleUserFactory.create(password='testing')
        self.user.is_staff = True
        self.user.is_superuser = False
        self.user.save()

        # Add 'Staff' group for user
        self.user.groups.add(Group.objects.get(name='Staff'))
        self.user.save()

        # Login user
        self.assertTrue(
            self.client.login(email=self.user.email, password='testing'))

    def tearDown(self):
        self.client.logout()
        self.user.delete()

    def test_staff_forbidden_access(self):
        response = self.client.get(reverse('admin:auth_group_changelist'))

        self.assertIsInstance(response, HttpResponseForbidden)

    def test_staff_create_project(self):
        response = self.client.get(reverse('admin:projects_project_add'))

        self.assertIsInstance(response, TemplateResponse)

    def test_superuser_access(self):
        self.client.logout()

        # Create staff user without superuser permission
        self.user = BlueBottleUserFactory.create(password='testing')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(
            self.client.login(email=self.user.email, password='testing'))

        response = self.client.get(reverse('admin:auth_group_changelist'))
        self.assertIsInstance(response, TemplateResponse)
