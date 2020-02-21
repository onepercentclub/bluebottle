from datetime import timedelta
import mock

from django.utils import timezone
from django.core import mail

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.models import Participant
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine
from bluebottle.activities.states import ReviewStateMachine, OrganizerStateMachine
from bluebottle.test.utils import BluebottleTestCase


class ActivityStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve()

        self.event = EventFactory.create(
            title='',
            duration=2,
            capacity=2,
            owner=self.initiative.owner,
            initiative=self.initiative
        )

    def test_create(self):
        event = EventFactory.create(initiative=self.initiative)

        self.assertEqual(event.review_status, ReviewStateMachine.approved.value)
        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_create_unapproved_initiative(self):
        initiative = InitiativeFactory.create()
        event = EventFactory.create(initiative=initiative)

        self.assertEqual(event.review_status, ReviewStateMachine.submitted.value)
        self.assertEqual(event.status, EventStateMachine.in_review.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

        initiative.states.submit()
        initiative.states.approve(save=True)

        event.refresh_from_db()

        self.assertEqual(event.review_status, ReviewStateMachine.approved.value)
        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer.refresh_from_db()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_create_incomplete(self):
        event = EventFactory.create(initiative=self.initiative, title='')

        self.assertEqual(event.review_status, ReviewStateMachine.draft.value)
        self.assertEqual(event.status, EventStateMachine.in_review.value)

        organizer = event.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

        event.title = 'Test title'
        event.save()

        self.assertEqual(event.review_status, ReviewStateMachine.approved.value)
        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer.refresh_from_db()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_full(self):
        event = EventFactory.create(initiative=self.initiative)
        ParticipantFactory.create_batch(event.capacity, activity=event)

        event.refresh_from_db()

        self.assertEqual(event.status, EventStateMachine.full.value)
        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_withdraw(self):
        event = EventFactory.create(initiative=self.initiative)
        ParticipantFactory.create(activity=event)

        participant = ParticipantFactory.create(activity=event)
        participant.states.withdraw(user=participant.user, save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.withdrawn.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_reject(self):
        event = EventFactory.create(initiative=self.initiative)
        ParticipantFactory.create(activity=event)

        participant = ParticipantFactory.create(activity=event)
        participant.states.reject(user=event.owner, save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.rejected.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_succeed(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() + timedelta(hours=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        future = timezone.now() + timedelta(hours=4)
        with mock.patch.object(timezone, 'now', return_value=future):
            event.save()

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_succeed_when_passed(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_succeed_change_start(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        event.start = timezone.now() + timedelta(hours=1)
        event.save()

        self.assertEqual(event.status, EventStateMachine.open.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

