from django.core import mail

from bluebottle.fsm import TransitionNotPossible
from bluebottle.initiatives.transitions import InitiativeTransitions
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory, OrganizationContactFactory


class InitiativeTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(InitiativeTransitionTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='Bart', last_name='Lacroix')
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            organization=None
        )

    def test_default_status(self):
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.draft
        )

    def test_submit(self):
        self.initiative.transitions.submit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_submit_incomplete(self):
        self.initiative.title = None

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_has_organization_missing(self):
        self.initiative.has_organization = True

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_has_organization_missing_contact(self):
        self.initiative.has_organization = True

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_has_organization_no_contact_name(self):
        self.initiative.has_organization = True
        self.initiative.organization = OrganizationFactory.create()
        self.initiative.organization_contact = OrganizationContactFactory.create(name=None)

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_has_organization(self):
        self.initiative.has_organization = True
        self.initiative.organization = OrganizationFactory.create()
        self.initiative.organization_contact = OrganizationContactFactory.create()
        self.initiative.transitions.submit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_submit_contact_without_phone(self):
        self.initiative.has_organization = True
        self.initiative.organization = OrganizationFactory.create()
        self.initiative.organization_contact = OrganizationContactFactory.create(
            phone=None
        )

        self.initiative.transitions.submit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_submit_contact_without_place(self):
        self.initiative.place = None
        self.initiative.save()
        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_contact_without_location_has_locations(self):
        LocationFactory.create_batch(5)
        self.initiative.place = None
        self.initiative.location = None
        self.initiative.save()
        self.assertRaises(
            TransitionNotPossible,
            self.initiative.transitions.submit
        )

    def test_submit_contact_with_location_has_locations(self):
        locations = LocationFactory.create_batch(5)
        self.initiative.place = None
        self.initiative.location = locations[0]
        self.initiative.save()
        self.initiative.transitions.submit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_needs_work(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.needs_work()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.needs_work
        )

    def test_resubmit(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.needs_work()
        self.initiative.transitions.resubmit()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )

    def test_approve(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.approved
        )
        self.assertEqual(len(mail.outbox), 1)
        subject = 'Your initiative {} has been approved!'.format(self.initiative.title)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertTrue('Hi Bart' in mail.outbox[0].body)

    def test_close(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.close()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.closed
        )
        self.assertEqual(len(mail.outbox), 1)
        subject = 'Your initiative {} has been closed'.format(self.initiative.title)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertTrue('Hi Bart' in mail.outbox[0].body)

    def test_reopen(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.close()
        self.initiative.transitions.reopen()
        self.assertEqual(
            self.initiative.status, InitiativeTransitions.values.submitted
        )
