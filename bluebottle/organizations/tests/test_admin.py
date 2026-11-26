from django.contrib.admin.sites import site
from django.urls import reverse

from bluebottle.activity_links.tests.factories import LinkedDeedFactory
from bluebottle.activity_pub.models import Accept
from bluebottle.activity_pub.tests.factories import FollowFactory
from bluebottle.activity_pub.tests.factories import OrganizationFactory as ActorFactory
from bluebottle.deeds.tests.factories import DeedFactory
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

    def test_linked_activities_inline(self):
        self.app.set_user(self.superuser)
        organization = OrganizationFactory.create(
            name='Dharma Initiative',
            website='http://dharma.in',
        )
        linked = LinkedDeedFactory.create(host_organization=organization, title='Linked hatch')
        other = LinkedDeedFactory.create(title='Somebody else')
        page = self.app.get(
            reverse('admin:organizations_organization_change', args=(organization.pk,))
        )
        self.assertIn('Linked hatch', page.text)
        self.assertNotIn('Somebody else', page.text)
        self.assertIn(
            reverse('admin:activity_links_linkeddeed_change', args=(linked.pk,)), page.text
        )
        self.assertNotEqual(linked.pk, other.pk)

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


class OrganizationAdminConnectTabTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.admin = site._registry[Organization]
        self.local_actor = ActorFactory.create()
        self.remote_actor = ActorFactory.create(iri='https://partner.example/organization/1')

    def page(self, organization):
        return self.app.get(
            reverse('admin:organizations_organization_change', args=(organization.pk,))
        )

    def test_no_tab_without_connect(self):
        organization = OrganizationFactory.create(website='http://dharma.in')
        page = self.page(organization)
        self.assertNotIn('field-connect_supplier', page.text)

    def test_local_actor(self):
        organization = self.local_actor.organization
        page = self.page(organization)
        self.assertIn('field-connect_supplier', page.text)
        self.assertEqual(str(self.admin.connect_local_actor(organization)), 'Yes')
        self.assertEqual(str(self.admin.connect_supplier(organization)), 'No')
        self.assertEqual(str(self.admin.connect_consumer(organization)), 'No')

    def test_remote_partner_without_connection(self):
        organization = self.remote_actor.organization
        self.assertEqual(str(self.admin.connect_local_actor(organization)), 'No')
        self.assertEqual(str(self.admin.connect_supplier(organization)), 'No')
        self.assertEqual(str(self.admin.connect_consumer(organization)), 'No')

    def test_supplier(self):
        organization = self.remote_actor.organization
        follow = FollowFactory.create(actor=self.local_actor, object=self.remote_actor)
        self.assertEqual(
            str(self.admin.connect_supplier(organization)), 'Yes, waiting for acceptance'
        )
        Accept.objects.create(object=follow, actor=self.remote_actor, iri='https://partner.example/accept/1')
        self.assertEqual(str(self.admin.connect_supplier(organization)), 'Yes')
        self.assertEqual(str(self.admin.connect_consumer(organization)), 'No')
        self.assertIn('field-connect_supplier', self.page(organization).text)

    def test_consumer(self):
        organization = self.remote_actor.organization
        follow = FollowFactory.create(
            actor=self.remote_actor, object=self.local_actor, iri='https://partner.example/follow/1'
        )
        Accept.objects.create(object=follow, actor=self.local_actor)
        self.assertEqual(str(self.admin.connect_consumer(organization)), 'Yes')
        self.assertEqual(str(self.admin.connect_supplier(organization)), 'No')

    def test_shared_and_adopted_activities(self):
        organization = self.remote_actor.organization
        self.assertEqual(self.admin.connect_shared_activities(organization), 0)
        self.assertEqual(self.admin.connect_adopted_activities(organization), 0)

        DeedFactory.create(host_organization=organization)
        self.assertEqual(self.admin.connect_adopted_activities(organization), 1)
        self.assertEqual(self.admin.connect_partner_activities(organization), 0)
