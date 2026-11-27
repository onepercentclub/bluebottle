from django.test import TestCase

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.organizations.models import OrganizationMember
from bluebottle.test.factory_models.organizations import (
    OrganizationContactFactory, OrganizationFactory, OrganizationMemberFactory
)


class InitiativeTestCase(TestCase):

    def test_status_changes(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        self.assertEqual(initiative.status, 'draft')

        initiative.states.submit(save=True)
        self.assertEqual(initiative.status, 'submitted')

        initiative.states.request_changes(save=True)
        self.assertEqual(initiative.status, 'needs_work')

        initiative.states.submit(save=True)
        self.assertEqual(initiative.status, 'submitted')

        initiative.states.approve(save=True)
        self.assertEqual(initiative.status, 'approved')

        initiative.states.cancel(save=True)
        self.assertEqual(initiative.status, 'cancelled')

        initiative.states.restore(save=True)
        self.assertEqual(initiative.status, 'needs_work')

    def test_activity_manager(self):
        initiative = InitiativeFactory(activity_managers=[])
        self.assertFalse(initiative.owner in initiative.activity_managers.all())

    def test_absolute_url(self):
        initiative = InitiativeFactory(activity_managers=[])
        expected = 'http://test.localhost/en/initiatives/details/{}/{}'.format(initiative.id, initiative.slug)
        self.assertEqual(initiative.get_absolute_url(), expected)

    def test_member_organization(self):
        membership = OrganizationMemberFactory.create()
        initiative = InitiativeFactory(has_organization=True, organization=None, owner=membership.member)
        self.assertEqual(initiative.organization, membership.organization)

    def test_member_preselect_organization(self):
        membership = OrganizationMemberFactory.create()
        initiative = InitiativeFactory(owner=membership.member, has_organization=None)
        self.assertEqual(initiative.organization, membership.organization)

    def test_member_organization_no_organizatoin(self):
        membership = OrganizationMemberFactory.create()
        initiative = InitiativeFactory(has_organization=False, organization=None, owner=membership.member)
        self.assertIsNone(initiative.organization)

    def test_member_organization_keeps_chosen_organization(self):
        membership = OrganizationMemberFactory.create()
        other = OrganizationFactory.create()
        initiative = InitiativeFactory(has_organization=True, organization=other, owner=membership.member)
        self.assertEqual(initiative.organization, other)

    def test_organization_does_not_create_membership(self):
        organization = OrganizationFactory.create()
        InitiativeFactory(has_organization=True, organization=organization)
        self.assertFalse(OrganizationMember.objects.exists())

    def test_owner_without_membership(self):
        initiative = InitiativeFactory(has_organization=None, organization=None)
        self.assertIsNone(initiative.organization)

    def test_organization_required(self):
        InitiativePlatformSettingsFactory.create(require_organization=True)

        initiative = InitiativeFactory()
        self.assertTrue(initiative.has_organization)

    def test_organization_not_required(self):
        InitiativePlatformSettingsFactory.create(require_organization=False)

        initiative = InitiativeFactory()
        self.assertFalse(initiative.has_organization)

    def test_organization_contact_already_set(self):
        organization_contact = OrganizationContactFactory.create()
        initiative = InitiativeFactory(
            has_organization=True,
            organization=OrganizationFactory.create(),
            organization_contact=organization_contact
        )
        self.assertEqual(
            initiative.organization_contact.pk,
            organization_contact.pk
        )

    def test_slug(self):
        initiative = InitiativeFactory(title='Test Title')
        self.assertEqual(
            initiative.slug, 'test-title'
        )

    def test_slug_empty(self):
        initiative = InitiativeFactory(title='')
        self.assertEqual(
            initiative.slug, 'new'
        )

    def test_slug_special_characters(self):
        initiative = InitiativeFactory(title='!!! $$$$')
        self.assertEqual(
            initiative.slug, 'new'
        )


class InitiativeSlugTestCase(TestCase):
    def test_long_title_produces_a_slug_that_fits(self):
        max_length = Initiative._meta.get_field('slug').max_length
        initiative = InitiativeFactory.create(title='a' * 255, slug='new')

        self.assertLessEqual(len(initiative.slug), max_length)
        self.assertFalse(initiative.slug.endswith('-'))
