from bluebottle.organizations.models import Organization

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory, OrganizationMemberFactory, OrganizationContactFactory
)
from bluebottle.test.utils import BluebottleTestCase


class OrganizationModelTest(BluebottleTestCase):
    def setUp(self):
        super(OrganizationModelTest, self).setUp()
        self.init_projects()

        for name in ['test', 'tast', 'tist', 'tust']:
            organization = OrganizationFactory.create(name=name)
            ProjectFactory(
                organization=organization
            )
            OrganizationMemberFactory.create(organization=organization)

    def test_merge(self):
        master = Organization.objects.get(name='test')

        master.merge(
            Organization.objects.filter(name__in=('tast', 'tist'))
        )

        self.assertEqual(len(Organization.objects.all()), 2)
        self.assertEqual(len(master.projects.all()), 3)
        self.assertEqual(len(master.members.all()), 3)

        not_merged = Organization.objects.get(name='tust')
        self.assertEqual(len(not_merged.projects.all()), 1)
        self.assertEqual(len(not_merged.members.all()), 1)


class OrganizationContactTest(BluebottleTestCase):
    def setUp(self):
        super(OrganizationContactTest, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.organization = OrganizationFactory.create()
        self.contact = OrganizationContactFactory.create(organization=self.organization,
                                                         owner=self.user)

    def test_organization_reference(self):
        contacts = self.organization.contacts
        self.assertEqual(contacts.count(), 1)
        self.assertEqual(contacts.all()[0].id, self.contact.id)


class OrganizationMemberTest(BluebottleTestCase):
    def setUp(self):
        super(OrganizationMemberTest, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.organization = OrganizationFactory.create()
        self.member = OrganizationMemberFactory.create(
            organization=self.organization,
            user=self.user
        )

    def test_organization_contact(self):
        self.assertTrue(
            len(self.user.organizationcontact_set.all()), 1
        )
        contact = self.user.organizationcontact_set.get()
        self.assertEqual(
            contact.email, self.user.email
        )
        self.assertEqual(
            contact.phone, self.user.phone_number
        )

    def test_organization_save_twice(self):
        self.member.save()
        self.assertTrue(
            len(self.user.organizationcontact_set.all()), 1
        )
        contact = self.user.organizationcontact_set.get()
        self.assertEqual(
            contact.email, self.user.email
        )
        self.assertEqual(
            contact.phone, self.user.phone_number
        )
