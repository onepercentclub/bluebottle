from django.core import mail

from bluebottle.events.tests.factories import EventFactory
from bluebottle.events.states import EventStateMachine
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.test.factory_models.organizations import OrganizationFactory, OrganizationContactFactory


class InitiativeReviewStateMachineTests(BluebottleTestCase):
    def setUp(self):
        super(InitiativeReviewStateMachineTests, self).setUp()
        self.user = BlueBottleUserFactory.create(first_name='Bart', last_name='Lacroix')
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            organization=None
        )

    def test_default_status(self):
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_create_incomplete(self):
        self.initiative = InitiativeFactory.create(
            title='',
            has_organization=False,
            owner=self.user,
            organization=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_make_complete(self):
        self.initiative = InitiativeFactory.create(
            title='',
            has_organization=False,
            owner=self.user,
            organization=None
        )
        self.initiative.title = 'Some title'
        self.initiative.save()

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_missing_organization(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_missing_organization_contact(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=OrganizationFactory.create(),
            organization_contact=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_missing_organization_contact_name(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=OrganizationFactory.create(),
            organization_contact=OrganizationContactFactory.create(name=None)
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_has_organization(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=OrganizationFactory.create(),
            organization_contact=OrganizationContactFactory.create()
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_has_organization_no_phone(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=OrganizationFactory.create(),
            organization_contact=OrganizationContactFactory.create(phone=None)
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_missing_place(self):
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            place=None,
            organization=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_submit_contact_without_location_has_locations(self):
        LocationFactory.create_batch(5)
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            place=None,
            location=None,
            organization=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
        )

    def test_submit_contact_location_has_locations(self):
        locations = LocationFactory.create_batch(5)
        self.initiative = InitiativeFactory.create(
            has_organization=False,
            owner=self.user,
            place=None,
            location=locations[0],
            organization=None
        )

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_needs_work(self):
        self.initiative.states.request_changes(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.needs_work.value
        )

    def test_resubmit(self):
        # FIXME
        # We have to figure out how we know the difference
        # between setting a initiative to 'needs work'
        # and resubmitting it. You don't want the initiative
        # to auto-resubmit if you save it in admin e.g.
        self.initiative.states.request_changes(save=True)
        self.initiative.title = 'Something else'
        self.initiative.save()
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_approve(self):
        self.initiative.states.approve(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.approved.value
        )
        self.assertEqual(len(mail.outbox), 1)
        subject = 'Your initiative "{}" has been approved!'.format(self.initiative.title)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertTrue('Hi Bart' in mail.outbox[0].body)

    def test_approve_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)

        self.initiative.states.approve(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.approved.value
        )

        event.refresh_from_db()
        self.assertEqual(
            event.status, EventStateMachine.open.value
        )

    def test_reject(self):
        self.initiative.states.reject(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.rejected.value
        )
        self.assertEqual(len(mail.outbox), 1)

        subject = 'Your initiative "{}" has been closed'.format(self.initiative.title)

        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertTrue('Hi Bart' in mail.outbox[0].body)

    def test_reject_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)
        self.initiative.states.reject(save=True)

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.rejected.value
        )

        event.refresh_from_db()

        self.assertEqual(
            event.status, EventStateMachine.rejected.value
        )

    def test_accept(self):
        self.initiative.states.reject()
        self.initiative.states.accept(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_accept_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)
        self.initiative.states.reject()
        self.initiative.states.accept(save=True)

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

        event.refresh_from_db()

        self.assertEqual(
            event.status, EventStateMachine.rejected.value
        )
