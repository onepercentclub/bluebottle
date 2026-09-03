from django.urls import reverse

from bluebottle.organizations.models import Organization
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
