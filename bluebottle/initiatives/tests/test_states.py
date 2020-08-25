from django.core import mail

from bluebottle.events.tests.factories import EventFactory
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory
from bluebottle.events.states import EventStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding_stripe.tests.factories import (
    StripePayoutAccountFactory,
    ExternalAccountFactory,
)
from bluebottle.fsm.state import TransitionNotPossible
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
        payout_account = StripePayoutAccountFactory.create(status='verified')
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account)

    def test_default_status(self):
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.draft.value
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

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
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
            self.initiative.status, ReviewStateMachine.draft.value
        )

        self.initiative.states.submit()
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

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
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
        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
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

        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
        )

    def test_has_organization(self):
        self.initiative = InitiativeFactory.create(
            has_organization=True,
            owner=self.user,
            organization=OrganizationFactory.create(),
            organization_contact=OrganizationContactFactory.create()
        )

        self.initiative.states.submit()
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

        self.initiative.states.submit()
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
        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
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
        self.assertRaises(
            TransitionNotPossible,
            self.initiative.states.submit
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

        self.initiative.states.submit()
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_submit_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)
        funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        BudgetLineFactory.create(activity=funding)

        incomplete_event = EventFactory.create(initiative=self.initiative, title='')
        self.initiative.states.submit(save=True)

        event.refresh_from_db()
        self.assertEqual(
            event.status, ReviewStateMachine.submitted.value
        )

        funding.refresh_from_db()
        self.assertEqual(
            funding.status, ReviewStateMachine.submitted.value
        )

        incomplete_event.refresh_from_db()
        self.assertEqual(
            incomplete_event.status, ReviewStateMachine.draft.value
        )

    def test_needs_work(self):
        self.initiative.states.submit()
        self.initiative.states.request_changes(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.needs_work.value
        )

    def test_needs_work_resubmit(self):
        self.initiative.states.submit()
        self.initiative.states.request_changes(save=True)
        self.initiative.title = 'Something else'
        self.initiative.save()
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.needs_work.value
        )

        self.initiative.states.submit(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.submitted.value
        )

    def test_approve(self):
        self.initiative.states.submit()
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
        incomplete_event = EventFactory.create(initiative=self.initiative, title='')
        funding = FundingFactory.create(initiative=self.initiative, bank_account=self.bank_account)
        BudgetLineFactory.create(activity=funding)

        self.initiative.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.approved.value
        )

        event.refresh_from_db()
        self.assertEqual(
            event.status, EventStateMachine.open.value
        )
        incomplete_event.refresh_from_db()
        self.assertEqual(
            incomplete_event.status, EventStateMachine.draft.value
        )
        funding.refresh_from_db()
        self.assertEqual(
            funding.status, FundingStateMachine.open.value
        )

    def test_reject(self):
        self.initiative.states.reject(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.rejected.value
        )
        self.assertEqual(len(mail.outbox), 1)

        subject = 'Your initiative "{}" has been rejected.'.format(self.initiative.title)

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

    def test_cancel(self):
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        mail.outbox = []
        self.initiative.states.cancel(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.cancelled.value
        )
        self.assertEqual(len(mail.outbox), 1)

        subject = 'The initiative "{}" has been cancelled.'.format(self.initiative.title)

        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertTrue('Hi Bart' in mail.outbox[0].body)

    def test_cancel_with_activities(self):
        self.initiative.states.submit(save=True)

        self.initiative.states.approve()

        event = EventFactory.create(initiative=self.initiative)
        event.states.submit(save=True)

        self.initiative.states.cancel(save=True)

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.cancelled.value
        )

        event.refresh_from_db()

        self.assertEqual(
            event.status, EventStateMachine.cancelled.value
        )

    def test_delete(self):
        self.initiative.states.delete(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.deleted.value
        )

    def test_delete_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)
        self.initiative.states.delete(save=True)

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.deleted.value
        )

        event.refresh_from_db()

        self.assertEqual(
            event.status, EventStateMachine.deleted.value
        )

    def test_restore(self):
        self.initiative.states.reject(save=True)
        self.initiative.states.restore(save=True)
        self.assertEqual(
            self.initiative.status, ReviewStateMachine.needs_work.value
        )

    def test_restore_with_activities(self):
        event = EventFactory.create(initiative=self.initiative)

        self.initiative.states.reject(save=True)
        self.initiative.states.restore(save=True)

        self.assertEqual(
            self.initiative.status, ReviewStateMachine.needs_work.value
        )

        event.refresh_from_db()

        self.assertEqual(
            event.status, EventStateMachine.needs_work.value
        )
