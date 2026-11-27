from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.cms.utils.color_contrast import DARK_NEUTRAL, WHITE, ensure_readable_fill
from bluebottle.organizations.models import OrganizationMember
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory, OrganizationMemberFactory
)
from bluebottle.test.utils import BluebottleTestCase


class OrganizationColorTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        SitePlatformSettings.objects.update(accessible_colours=False)

    def test_text_color_white_on_dark(self):
        organization = OrganizationFactory.create(color='#00305E')

        self.assertEqual(organization.background_color, '#00305E')
        self.assertEqual(organization.text_color, WHITE)

    def test_text_color_dark_on_light(self):
        organization = OrganizationFactory.create(color='#FFFFFF')

        self.assertEqual(organization.background_color, '#FFFFFF')
        self.assertEqual(organization.text_color, DARK_NEUTRAL)

    def test_accessible_colours_darkens_light_fill(self):
        SitePlatformSettings.objects.update(accessible_colours=True)
        organization = OrganizationFactory.create(color='#A2A2A2')

        expected = ensure_readable_fill('#A2A2A2')
        self.assertEqual(organization.background_color, expected)
        self.assertNotEqual(organization.background_color, '#A2A2A2')
        self.assertEqual(organization.text_color, WHITE)

    def test_no_color_returns_none(self):
        organization = OrganizationFactory.create(color=None)
        self.assertIsNone(organization.background_color)
        self.assertIsNone(organization.text_color)


class OrganizationMemberTestCase(BluebottleTestCase):

    def test_default_role_is_member(self):
        membership = OrganizationMemberFactory.create()
        self.assertEqual(membership.role, OrganizationMember.Roles.member)

    def test_member_organization(self):
        membership = OrganizationMemberFactory.create()
        self.assertEqual(membership.member.organization, membership.organization)

    def test_member_without_organization(self):
        self.assertIsNone(BlueBottleUserFactory.create().organization)

    def test_same_member_and_organization_only_once(self):
        membership = OrganizationMemberFactory.create()
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                OrganizationMemberFactory.create(
                    member=membership.member, organization=membership.organization
                )

    def test_member_cannot_join_second_organization(self):
        membership = OrganizationMemberFactory.create()
        second = OrganizationMemberFactory.build(
            member=membership.member, organization=OrganizationFactory.create()
        )
        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_member_can_be_moved_to_other_organization(self):
        membership = OrganizationMemberFactory.create()
        membership.organization = OrganizationFactory.create()
        membership.full_clean()
        membership.save()
        self.assertEqual(membership.member.organization, membership.organization)

    def test_members_of_same_organization(self):
        organization = OrganizationFactory.create()
        OrganizationMemberFactory.create_batch(2, organization=organization)
        self.assertEqual(organization.members.count(), 2)

    def test_creating_organization_does_not_create_membership(self):
        organization = OrganizationFactory.create()
        self.assertEqual(organization.members.count(), 0)
        self.assertIsNone(organization.owner.organization)

    def test_deleting_organization_keeps_member(self):
        membership = OrganizationMemberFactory.create()
        member = membership.member
        membership.organization.delete()
        member.refresh_from_db()
        self.assertEqual(member.organization_memberships.count(), 0)
