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

    def changelist(self, **params):
        return self.app.get(
            reverse('admin:organizations_organization_changelist'), params
        )

    def test_changelist_hides_archived_by_default(self):
        OrganizationFactory.create(name='Active org', website='http://active.org')
        OrganizationFactory.create(name='Archived org', website='http://archived.org', archived=True)

        page = self.changelist()
        self.assertIn('Active org', page.text)
        self.assertNotIn('Archived org', page.text)

    def test_changelist_filter_archived(self):
        OrganizationFactory.create(name='Active org', website='http://active.org')
        OrganizationFactory.create(name='Archived org', website='http://archived.org', archived=True)

        page = self.changelist(archived='1')
        self.assertNotIn('Active org', page.text)
        self.assertIn('Archived org', page.text)

    def test_changelist_filter_all(self):
        OrganizationFactory.create(name='Active org', website='http://active.org')
        OrganizationFactory.create(name='Archived org', website='http://archived.org', archived=True)

        page = self.changelist(archived='all')
        self.assertIn('Active org', page.text)
        self.assertIn('Archived org', page.text)

    def test_archived_filter_defaults_to_no(self):
        page = self.changelist()
        selected = page.html.find('li', {'class': 'selected'})
        self.assertIsNotNone(selected)
        self.assertEqual(selected.text.strip(), 'No')

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
        self.assertTrue(page.html.find(attrs={'data-field-id': 'id_color'}))
        self.assertTrue(page.html.find(id='id_color'))
        self.assertIn('solid_color_contrast.js', page.text)
