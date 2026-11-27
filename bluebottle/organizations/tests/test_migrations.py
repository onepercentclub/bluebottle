from importlib import import_module

from django.apps import apps
from django.core import mail

from bluebottle.organizations.models import OrganizationMember
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase

migration = import_module(
    'bluebottle.organizations.migrations.0030_convert_partner_organization_to_members'
)


class ConvertPartnerOrganizationTestCase(BluebottleTestCase):

    def convert(self):
        migration.convert_partner_organization(apps, None)

    def test_member_with_partner_organization_becomes_member(self):
        organization = OrganizationFactory.create()
        member = BlueBottleUserFactory.create(partner_organization=organization)

        self.convert()

        membership = OrganizationMember.objects.get()
        self.assertEqual(membership.member, member)
        self.assertEqual(membership.organization, organization)
        self.assertEqual(membership.role, OrganizationMember.Roles.member)

    def test_creator_of_organization_does_not_become_member(self):
        organization = OrganizationFactory.create()
        organization.owner.partner_organization = organization
        organization.owner.save()

        self.convert()

        self.assertEqual(OrganizationMember.objects.count(), 0)

    def test_other_member_of_same_organization_does_become_member(self):
        organization = OrganizationFactory.create()
        organization.owner.partner_organization = organization
        organization.owner.save()
        colleague = BlueBottleUserFactory.create(partner_organization=organization)

        self.convert()

        self.assertEqual(OrganizationMember.objects.get().member, colleague)

    def test_member_without_partner_organization_is_ignored(self):
        BlueBottleUserFactory.create()

        self.convert()

        self.assertEqual(OrganizationMember.objects.count(), 0)

    def test_conversion_is_idempotent(self):
        BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())

        self.convert()
        self.convert()

        self.assertEqual(OrganizationMember.objects.count(), 1)

    def test_conversion_sends_no_email(self):
        BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())
        mail.outbox = []

        self.convert()

        self.assertEqual(len(mail.outbox), 0)
