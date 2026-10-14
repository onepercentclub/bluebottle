from django.urls import reverse

from bluebottle.organizations.models import Organization
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class OrganizationAdminTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)

    def test_admin_create_organization_without_website(self):
        url = reverse('admin:organizations_organization_changelist')
        page = self.app.get(url)
        page = page.click('Add organisation')
        form = page.forms['organization_form']
        form['name'] = 'Dharma Initiative'
        page = form.submit()
        self.assertEqual(Organization.objects.count(), 0)
        self.assertEqual(page.html.find("p", {'class': 'errornote'}).text.strip(), 'Please correct the error below.')

    def test_admin_create_organization(self):
        url = reverse('admin:organizations_organization_changelist')
        page = self.app.get(url)
        page = page.click('Add organisation')
        form = page.forms['organization_form']
        form['name'] = 'Dharma Initiative'
        form['website'] = 'http://dharma.in'
        page = form.submit().follow()
        self.assertEqual(Organization.objects.count(), 1)
        self.assertIsNone(page.html.find("p", {'class': 'errornote'}))

    def test_view_on_site_link(self):
        organization = OrganizationFactory.create(
            name='Dharma Initiative',
            website='http://dharma.in',
        )
        url = reverse(
            'admin:organizations_organization_change',
            args=(organization.pk,),
        )
        page = self.app.get(url)
        self.assertIn('View on site', page.text)
        self.assertTrue(page.html.find('a', {'class': 'viewsitelink'}))
        self.assertEqual(
            organization.get_absolute_url(),
            'http://test.localhost/en/organizations/{}/{}/activities/list'.format(
                organization.pk,
                organization.slug,
            ),
        )

    def test_color_contrast_preview(self):
        organization = OrganizationFactory.create(
            name='Dharma Initiative',
            website='http://dharma.in',
            color='#00305E',
        )
        url = reverse(
            'admin:organizations_organization_change',
            args=(organization.pk,),
        )
        page = self.app.get(url)
        self.assertTrue(page.html.find(id='organization-color-contrast-panel'))
        self.assertTrue(page.html.find(id='id_color'))
        self.assertIn('organization_color_contrast.js', page.text)
