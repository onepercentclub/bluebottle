from django.test import TestCase

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory


class InitiativeTestCase(TestCase):

    def test_properties(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        expected = '/initiatives/details/{}/dharma-initiative/'.format(initiative.id)
        self.assertEqual(initiative.full_url, expected)

    def test_status_changes(self):
        initiative = InitiativeFactory.create(title='Dharma initiative')
        self.assertEqual(initiative.status, 'draft')

        initiative.transitions.submit()
        self.assertEqual(initiative.status, 'submitted')

        initiative.transitions.needs_work()
        self.assertEqual(initiative.status, 'needs_work')

        initiative.transitions.resubmit()
        self.assertEqual(initiative.status, 'submitted')

        initiative.transitions.approve()
        self.assertEqual(initiative.status, 'approved')

        initiative.transitions.close()
        self.assertEqual(initiative.status, 'closed')

        initiative.transitions.reopen()
        self.assertEqual(initiative.status, 'submitted')

    def test_activity_manager(self):
        initiative = InitiativeFactory(activity_manager=None)

        self.assertEqual(initiative.owner, initiative.activity_manager)

    def test_full_url(self):
        initiative = InitiativeFactory(activity_manager=None, slug='test-initiative')

        self.assertEqual(
            initiative.full_url,
            '/initiatives/details/{}/test-initiative/'.format(initiative.pk)
        )

    def test_member_organization(self):
        member = BlueBottleUserFactory.create(partner_organization=OrganizationFactory.create())
        initiative = InitiativeFactory(has_organization=True, organization=None, owner=member)

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
