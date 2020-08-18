from django.test import TestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory, OrganizationContactFactory


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

        initiative.states.reject(save=True)
        self.assertEqual(initiative.status, 'rejected')

        initiative.states.restore(save=True)
        self.assertEqual(initiative.status, 'needs_work')

    def test_activity_manager(self):
        initiative = InitiativeFactory(activity_manager=None)
        self.assertEqual(initiative.owner, initiative.activity_manager)

    def test_absolute_url(self):
        initiative = InitiativeFactory(activity_manager=None)
        expected = 'http://testserver/en/initiatives/details/{}/{}'.format(initiative.id, initiative.slug)
        self.assertEqual(initiative.get_absolute_url(), expected)

    def test_member_organization(self):
        member = BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())
        initiative = InitiativeFactory(has_organization=True, organization=None, owner=member)
        self.assertEqual(initiative.organization, member.partner_organization)

    def test_member_preselect_organization(self):
        member = BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())
        initiative = InitiativeFactory(owner=member, has_organization=None)
        self.assertEqual(initiative.organization, member.partner_organization)

    def test_member_organization_no_organizatoin(self):
        member = BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())
        initiative = InitiativeFactory(has_organization=False, organization=None, owner=member)
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
