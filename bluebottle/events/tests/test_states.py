from datetime import timedelta
import mock

from django.utils import timezone

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.models import Participant
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.test.utils import BluebottleTestCase


class ActivityStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)

    def test_create(self):
        event = EventFactory.create(initiative=self.initiative)

        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_reject(self):
        event = EventFactory.create(initiative=self.initiative)
        event.states.reject(save=True)

        self.assertEqual(event.status, EventStateMachine.rejected.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def test_accept(self):
        event = EventFactory.create(initiative=self.initiative)
        event.states.reject(save=True)
        event.states.accept(save=True)

        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_create_unapproved_initiative(self):
        initiative = InitiativeFactory.create()
        event = EventFactory.create(initiative=initiative)

        self.assertEqual(event.status, EventStateMachine.submitted.value)

        organizer = event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

        initiative.states.approve(save=True)

        event.refresh_from_db()

        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer.refresh_from_db()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_create_incomplete(self):
        event = EventFactory.create(initiative=self.initiative, title='')

        self.assertEqual(event.status, EventStateMachine.draft.value)

        organizer = event.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

        event.title = 'Test title'
        event.save()

        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer.refresh_from_db()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_not_full(self):
        event = EventFactory.create(initiative=self.initiative, capacity=10)
        ParticipantFactory.create_batch(event.capacity - 1, activity=event)

        event.refresh_from_db()

        self.assertEqual(event.status, EventStateMachine.open.value)
        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_full(self):
        event = EventFactory.create(initiative=self.initiative, capacity=10)
        ParticipantFactory.create_batch(event.capacity, activity=event)

        event.refresh_from_db()

        self.assertEqual(event.status, EventStateMachine.full.value)
        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_change_capacity_full(self):
        event = EventFactory.create(initiative=self.initiative, capacity=10)
        ParticipantFactory.create_batch(event.capacity - 1, activity=event)
        self.assertEqual(event.status, EventStateMachine.open.value)

        event.capacity = event.capacity - 1

        effects = list(event.current_effects)
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].name, 'fill')

        event.save()
        self.assertEqual(event.status, EventStateMachine.full.value)

    def test_change_capacity_open(self):
        event = EventFactory.create(initiative=self.initiative, capacity=10)
        ParticipantFactory.create_batch(event.capacity, activity=event)

        event.capacity = event.capacity + 1

        effects = list(event.current_effects)
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].name, 'unfill')

        event.save()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_change_capacity_no_transition(self):
        event = EventFactory.create(initiative=self.initiative, capacity=10)
        ParticipantFactory.create_batch(event.capacity - 1, activity=event)

        event.capacity = event.capacity + 1
        event.save()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_withdraw(self):
        event = EventFactory.create(initiative=self.initiative)
        self.assertEqual(event.status, EventStateMachine.open.value)

        participants = ParticipantFactory.create_batch(event.capacity, activity=event)
        self.assertEqual(event.status, EventStateMachine.full.value)

        participant = participants[0]
        participant.states.withdraw(user=participant.user)

        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.withdrawn.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_reject_participants(self):
        event = EventFactory.create(initiative=self.initiative)
        self.assertEqual(event.status, EventStateMachine.open.value)

        participants = ParticipantFactory.create_batch(event.capacity, activity=event)
        self.assertEqual(event.status, EventStateMachine.full.value)

        participant = participants[0]
        participant.states.reject(user=event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.rejected.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_mark_absent(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            duration=1
        )
        participant = ParticipantFactory.create(activity=event)
        self.assertEqual(event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.no_show.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.closed.value)

    def test_mark_absent_no_change(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)
        participant = ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.no_show.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.succeeded.value)

    def test_mark_present(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            duration=1
        )
        participant = ParticipantFactory.create(activity=event)
        self.assertEqual(event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=event.owner)
        participant.save()

        participant.states.mark_present(user=event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

        event.refresh_from_db()
        self.assertEqual(event.status, EventStateMachine.succeeded.value)

    def test_succeed_in_future(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() + timedelta(days=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        future = timezone.now() + timedelta(days=2)
        with mock.patch.object(timezone, 'now', return_value=future):
            event.save()

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        event.refresh_from_db()
        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_succeed_when_passed(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_failed_when_passed(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )

        self.assertEqual(event.status, EventStateMachine.closed.value)

    def test_not_succeed_change_start(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() + timedelta(hours=1),
            duration=1
        )
        self.assertEqual(event.status, EventStateMachine.open.value)
        ParticipantFactory.create(activity=event)

        event.start = timezone.now() + timedelta(hours=2)
        event.save()

        self.assertEqual(event.status, EventStateMachine.open.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_succeed_change_start(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() + timedelta(hours=1),
            duration=1
        )
        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, EventStateMachine.open.value)

        event.start = timezone.now() - timedelta(hours=2)
        event.save()

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_change_start_reopen_from_closed(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )

        self.assertEqual(event.status, EventStateMachine.closed.value)

        event.start = timezone.now() + timedelta(hours=2)
        event.save()

        self.assertEqual(event.status, EventStateMachine.open.value)

    def test_change_start_reopen_from_succeeded(self):
        event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(hours=1),
            duration=1
        )

        ParticipantFactory.create(activity=event)

        self.assertEqual(event.status, EventStateMachine.succeeded.value)

        event.start = timezone.now() + timedelta(hours=2)
        event.save()

        self.assertEqual(event.status, EventStateMachine.open.value)

        for participant in event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)
