from datetime import timedelta
import mock

from django.core import mail
from django.utils import timezone

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.models import Participant
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.test.utils import BluebottleTestCase


class ActivityStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory.create(
            initiative=self.initiative,
            capacity=10,
            duration=1
        )
        self.passed_event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            duration=1
        )

    def test_create(self):
        self.assertEqual(self.event.status, EventStateMachine.draft.value)

        organizer = self.event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

    def test_submit(self):
        self.event.states.submit(save=True)
        self.assertEqual(self.event.status, EventStateMachine.open.value)

        organizer = self.event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_reject(self):
        self.event.states.submit(save=True)
        self.event.states.reject(save=True)

        self.assertEqual(self.event.status, EventStateMachine.rejected.value)

        organizer = self.event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def test_restore(self):
        self.event.states.submit(save=True)
        self.event.states.reject(save=True)
        self.event.states.restore(save=True)
        self.event.states.submit(save=True)

        self.assertEqual(self.event.status, EventStateMachine.open.value)

        organizer = self.event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_create_unapproved_initiative(self):
        initiative = InitiativeFactory.create()
        initiative.states.submit(save=True)
        event = EventFactory.create(initiative=initiative)

        event.states.submit(save=True)
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
        self.assertRaises(
            TransitionNotPossible,
            event.states.submit
        )

        organizer = event.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.new.value)

        event.title = 'Test title'
        event.states.submit(save=True)

        self.assertEqual(event.status, EventStateMachine.open.value)

        organizer.refresh_from_db()

        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_not_full(self):
        self.event.states.submit(save=True)

        ParticipantFactory.create_batch(self.event.capacity - 1, activity=self.event)

        self.event.refresh_from_db()

        self.assertEqual(self.event.status, EventStateMachine.open.value)
        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_full(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create_batch(self.event.capacity, activity=self.event)

        self.event.refresh_from_db()

        self.assertEqual(self.event.status, EventStateMachine.full.value)
        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_change_capacity_full(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create_batch(self.event.capacity - 1, activity=self.event)
        self.assertEqual(self.event.status, EventStateMachine.open.value)

        self.event.capacity = self.event.capacity - 1

        effects = list(self.event.current_effects)
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].name, 'fill')

        self.event.save()
        self.assertEqual(self.event.status, EventStateMachine.full.value)

    def test_change_capacity_open(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create_batch(self.event.capacity, activity=self.event)

        self.event.capacity = self.event.capacity + 1

        effects = list(self.event.current_effects)
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].name, 'unfill')

        self.event.save()
        self.assertEqual(self.event.status, EventStateMachine.open.value)

    def test_change_capacity_no_transition(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create_batch(self.event.capacity - 1, activity=self.event)

        self.event.capacity = self.event.capacity + 1
        self.event.save()
        self.assertEqual(self.event.status, EventStateMachine.open.value)

    def test_withdraw(self):
        self.event.states.submit(save=True)
        participants = ParticipantFactory.create_batch(self.event.capacity, activity=self.event)
        self.assertEqual(self.event.status, EventStateMachine.full.value)

        participant = participants[0]
        participant.states.withdraw(user=participant.user)

        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.withdrawn.value)

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, EventStateMachine.open.value)

    def test_reject_participants(self):
        self.event.states.submit(save=True)
        participants = ParticipantFactory.create_batch(self.event.capacity, activity=self.event)
        self.assertEqual(self.event.status, EventStateMachine.full.value)

        participant = participants[0]
        participant.states.reject(user=self.event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.rejected.value)

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, EventStateMachine.open.value)

    def test_mark_absent(self):
        self.event.states.submit(save=True)
        participant = ParticipantFactory.create(activity=self.passed_event)
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=self.passed_event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.no_show.value)

        self.passed_event.refresh_from_db()
        self.assertEqual(self.passed_event.status, EventStateMachine.closed.value)

    def test_mark_absent_no_change(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create(activity=self.passed_event)
        participant = ParticipantFactory.create(activity=self.passed_event)

        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=self.passed_event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.no_show.value)

        self.passed_event.refresh_from_db()
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

    def test_mark_present(self):
        self.event.states.submit(save=True)
        participant = ParticipantFactory.create(activity=self.passed_event)
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)
        self.assertEqual(participant.status, EventStateMachine.succeeded.value)

        participant.states.mark_absent(user=self.passed_event.owner)
        participant.save()

        participant.states.mark_present(user=self.passed_event.owner)
        participant.save()

        self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

        self.passed_event.refresh_from_db()
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

    def test_succeed_in_future(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create(activity=self.event)

        future = self.event.start + timedelta(days=2)
        with mock.patch.object(timezone, 'now', return_value=future):
            self.event.save()

        self.assertEqual(self.event.status, EventStateMachine.succeeded.value)

        self.event.refresh_from_db()
        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)
            self.assertEqual(participant.time_spent, self.event.duration)

    def test_succeed_when_passed(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create(activity=self.passed_event)

        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

        for participant in self.passed_event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_failed_when_passed(self):
        self.event.states.submit(save=True)
        self.assertEqual(self.passed_event.status, EventStateMachine.closed.value)

    def test_not_succeed_change_start(self):
        self.event.states.submit(save=True)
        self.assertEqual(self.event.status, EventStateMachine.open.value)
        ParticipantFactory.create(activity=self.event)

        self.event.start = timezone.now() + timedelta(hours=2)
        self.event.save()

        self.assertEqual(self.event.status, EventStateMachine.open.value)

        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)

    def test_succeed_change_start(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create(activity=self.event)

        self.assertEqual(self.event.status, EventStateMachine.open.value)

        self.event.start = timezone.now() - timedelta(hours=2)

        self.event.save()

        self.assertEqual(self.event.status, EventStateMachine.succeeded.value)

        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)
            self.assertEqual(participant.time_spent, self.event.duration)

    def test_change_start_reopen_from_closed(self):
        self.event.states.submit(save=True)
        self.assertEqual(self.passed_event.status, EventStateMachine.closed.value)

        self.passed_event.start = timezone.now() + timedelta(hours=2)
        self.passed_event.save()

        self.assertEqual(self.passed_event.status, EventStateMachine.open.value)

    def test_change_start_reopen_from_succeeded(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create(activity=self.passed_event)

        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

        self.passed_event.start = timezone.now() + timedelta(hours=2)
        self.passed_event.save()

        self.assertEqual(self.passed_event.status, EventStateMachine.open.value)

        for participant in self.passed_event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)


class ParticipantStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory.create(
            initiative=self.initiative,
            capacity=10,
            duration=1
        )
        self.participant = ParticipantFactory.create(activity=self.event)

        self.passed_event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            duration=1
        )

        self.passed_participant = ParticipantFactory.create(activity=self.passed_event)

    def messages(self, user):
        return [
            message
            for message in mail.outbox
            if message.recipients()[0] == user.email
        ]

    def test_created(self):
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertEqual(self.participant.time_spent, 0)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.participant.user)), 1
        )

    def test_withdraw(self):
        self.participant.states.withdraw(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.withdrawn.value)
        self.assertFalse(
            self.event.followers.filter(user=self.participant.user).exists()
        )

        self.assertEqual(
            len(self.messages(self.participant.user)), 1
        )

    def test_reapply(self):
        self.participant.states.withdraw(save=True)
        self.participant.states.reapply(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.participant.user)), 1
        )

    def test_reject(self):
        self.participant.states.reject(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.rejected.value)
        self.assertFalse(
            self.event.followers.filter(user=self.participant.user).exists()
        )

        self.assertEqual(
            len(self.messages(self.participant.user)), 2
        )

    def test_reaccept(self):
        self.participant.states.reject(save=True)
        self.participant.states.reaccept(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )

        self.assertEqual(
            len(self.messages(self.participant.user)), 2
        )

    def test_created_passed(self):
        self.assertEqual(self.passed_participant.status, ParticipantStateMachine.succeeded.value)
        self.assertEqual(self.passed_participant.time_spent, self.passed_event.duration)

        self.assertTrue(
            self.passed_event.followers.filter(user=self.passed_participant.user).exists()
        )

        self.event.refresh_from_db()
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

        self.assertEqual(
            len(self.messages(self.passed_participant.user)), 1
        )

    def test_mark_absent(self):
        self.passed_participant.states.mark_absent(save=True)

        self.assertEqual(self.passed_participant.status, ParticipantStateMachine.no_show.value)
        self.assertEqual(self.passed_participant.time_spent, 0)
        self.assertFalse(
            self.passed_event.followers.filter(user=self.passed_participant.user).exists()
        )

        self.assertEqual(
            len(self.messages(self.passed_participant.user)), 1
        )

    def test_mark_present(self):
        self.passed_participant.states.mark_absent(save=True)
        self.passed_participant.states.mark_present(save=True)

        self.assertEqual(self.passed_participant.status, ParticipantStateMachine.succeeded.value)
        self.assertEqual(self.passed_participant.time_spent, self.passed_event.duration)

        self.assertTrue(
            self.passed_event.followers.filter(user=self.passed_participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.passed_participant.user)), 1
        )

    def test_reset(self):
        self.passed_event.start = timezone.now() + timedelta(days=1)
        self.passed_event.save()

        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertEqual(self.participant.time_spent, 0)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
