from mock import patch

from django.core.urlresolvers import reverse
from django.contrib import admin

from bluebottle.organizations.models import Organization

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase


class AdminMergeOrganizationsTest(BluebottleTestCase):
    """
    Test the admin organization merge functionality
    """

    def setUp(self):
        super(AdminMergeOrganizationsTest, self).setUp()
        self.init_projects()

        for name in ['test', 'tast', 'tist']:
            organization = OrganizationFactory.create(name=name)
            ProjectFactory(
                title='project for {}'.format(name),
                organization=organization
            )

        self.admin_url = reverse('admin:organizations_organization_changelist')
        self.client.force_login(BlueBottleUserFactory.create(is_staff=True, is_superuser=True))

    def test_render_pick(self):
        response = self.client.post(
            self.admin_url, {
                'action': 'merge',
                admin.ACTION_CHECKBOX_NAME: [
                    organization.pk for organization in Organization.objects.all()
                ]
            },
            format='multipart'
        )
        self.assertTemplateUsed(response, 'admin/merge_preview.html')

    def test_render_merge(self):
        master = Organization.objects.all()[0]
        response = self.client.post(
            self.admin_url, {
                'action': 'merge',
                'master': master.pk,
                admin.ACTION_CHECKBOX_NAME: [
                    organization.pk for organization in Organization.objects.all()
                ]
            },
            format='multipart'
        )

        self.assertRedirects(response, self.admin_url)

        merged = Organization.objects.get()
        self.assertEqual(merged.pk, master.pk)
        self.assertEqual(len(merged.projects.all()), 3)

    def test_redirect_with_one_organization(self):
        with patch('django.contrib.messages.add_message') as add_message_mock:
            response = self.client.post(
                self.admin_url, {
                    'action': 'merge',
                    admin.ACTION_CHECKBOX_NAME: [
                        organization.pk for organization in Organization.objects.all()[:1]
                    ]
                },
                format='multipart'
            )
        self.assertRedirects(response, self.admin_url)
        add_message_mock.assert_called()
