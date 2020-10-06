# -*- coding: utf-8 -*-
from bluebottle.clients.utils import LocalTenant

from bluebottle.events.tasks import event_tasks
from datetime import timedelta
import mock

from django.core import mail
from django.utils import timezone
from django.utils.timezone import now

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.models import Participant
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from django.db import connection


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

    def test_submit_unsubmitted_initiative(self):
        initiative = InitiativeFactory.create()
        event = EventFactory.create(initiative=initiative)

        self.assertRaises(
            TransitionNotPossible,
            event.states.submit
        )

    def test_reject(self):
        self.event.states.reject(save=True)
        self.assertEqual(self.event.status, EventStateMachine.rejected.value)
        organizer = self.event.contributions.get()

        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def test_cancel(self):
        self.event.states.submit(save=True)
        self.event.states.cancel(save=True)

        self.assertEqual(self.event.status, EventStateMachine.cancelled.value)
        self.assertEqual(
            mail.outbox[1].subject,
            'Your event "{}" has been cancelled'.format(self.event.title)
        )
        self.assertTrue(
            u'Unfortunately your event “{}” has been cancelled.'.format(
                self.event.title
            )
            in mail.outbox[1].body
        )

    def test_restore(self):
        self.event.states.reject(save=True)
        self.event.states.restore(save=True)
        self.assertEqual(self.event.status, EventStateMachine.needs_work.value)
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
        self.assertEqual(effects[0].name, 'lock')

        self.event.save()
        self.assertEqual(self.event.status, EventStateMachine.full.value)

    def test_change_capacity_open(self):
        self.event.states.submit(save=True)
        ParticipantFactory.create_batch(self.event.capacity, activity=self.event)

        self.event.capacity = self.event.capacity + 1

        effects = list(self.event.current_effects)
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].name, 'reopen')

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

    def test_reject_participants_succeeded(self):
        self.event.states.submit(save=True)
        self.assertEqual(self.event.status, EventStateMachine.open.value)
        participant = ParticipantFactory.create(activity=self.event)
        participant.states.reject(user=self.event.owner, save=True)
        self.assertEqual(participant.status, ParticipantStateMachine.rejected.value)

        self.event.refresh_from_db()
        self.event.start = timezone.now() - timedelta(hours=2)
        self.event.save()

        self.assertEqual(self.event.status, EventStateMachine.cancelled.value)

        participant.states.accept(save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, EventStateMachine.succeeded.value)

    def test_withdraw_participants_succeeded(self):
        self.event.states.submit(save=True)
        participants = ParticipantFactory.create_batch(self.event.capacity, activity=self.event)
        self.assertEqual(self.event.status, EventStateMachine.full.value)

        participant = participants[0]
        participant.states.withdraw(user=participant.user, save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.withdrawn.value)

        self.event.refresh_from_db()
        self.event.start = timezone.now() - timedelta(hours=2)
        self.event.save()

        self.assertEqual(self.event.status, EventStateMachine.succeeded.value)

        participant.states.reapply(save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_mark_absent(self):
        self.passed_event.states.submit(save=True)
        participant = ParticipantFactory.create(activity=self.passed_event)
        participant.states.mark_absent(user=self.passed_event.owner, save=True)

        self.assertEqual(participant.status, ParticipantStateMachine.no_show.value)
        self.passed_event.refresh_from_db()

        self.assertEqual(self.passed_event.status, EventStateMachine.cancelled.value)

    def test_mark_absent_no_change(self):
        self.passed_event.states.submit(save=True)
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
        self.passed_event.states.submit(save=True)
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
        self.event.save()
        tenant = connection.tenant
        with mock.patch.object(timezone, 'now', return_value=future):
            event_tasks()
        with LocalTenant(tenant, clear_tenant=True):
            self.event.refresh_from_db()

        self.assertEqual(self.event.status, EventStateMachine.succeeded.value)

        self.event.refresh_from_db()
        for participant in self.event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)
            self.assertEqual(participant.time_spent, self.event.duration)

    def test_succeed_when_passed(self):
        self.passed_event.states.submit(save=True)
        ParticipantFactory.create(activity=self.passed_event)
        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

        for participant in self.passed_event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.succeeded.value)

    def test_failed_when_passed(self):
        self.passed_event.states.submit(save=True)
        self.passed_event.refresh_from_db()
        self.assertEqual(self.passed_event.status, EventStateMachine.cancelled.value)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject,
            'Your event "{}" has been cancelled'.format(self.passed_event.title)
        )
        self.assertTrue(
            u'Unfortunately, nobody joined your event “{}”'.format(self.passed_event.title)
            in mail.outbox[1].body
        )

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

    def test_change_start_reopen_from_cancelled(self):
        self.passed_event.states.submit(save=True)
        self.assertEqual(self.passed_event.status, EventStateMachine.cancelled.value)

        self.passed_event.start = timezone.now() + timedelta(hours=2)
        self.passed_event.save()

        self.assertEqual(self.passed_event.status, EventStateMachine.open.value)

    def test_change_start_reopen_from_succeeded(self):
        self.passed_event.states.submit(save=True)
        ParticipantFactory.create(activity=self.passed_event)

        self.assertEqual(self.passed_event.status, EventStateMachine.succeeded.value)

        self.passed_event.start = timezone.now() + timedelta(hours=2)
        self.passed_event.save()

        self.assertEqual(self.passed_event.status, EventStateMachine.open.value)

        for participant in self.passed_event.contributions.instance_of(Participant):
            self.assertEqual(participant.status, ParticipantStateMachine.new.value)


class ParticipantStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiator = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.initiator)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory.create(
            initiative=self.initiative,
            owner=self.initiator,
            capacity=10,
            duration=1,
            start=now() + timedelta(hours=4)
        )
        self.user = BlueBottleUserFactory.create()
        self.old_user = BlueBottleUserFactory.create()

        self.passed_event = EventFactory.create(
            initiative=self.initiative,
            start=timezone.now() - timedelta(days=1),
            status='succeeded',
            duration=1
        )
        mail.outbox = []
        self.participant = ParticipantFactory.create(user=self.user, activity=self.event)
        self.passed_participant = ParticipantFactory.create(user=self.old_user, activity=self.passed_event)

    def messages(self, user):
        return [
            message
            for message in mail.outbox
            if message.recipients()[0] == user.email
        ]

    def test_join(self):
        self.assertEqual(self.passed_participant.status, ParticipantStateMachine.succeeded.value)
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertEqual(self.participant.time_spent, 0)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.user)), 1
        )
        self.assertEqual(
            len(self.messages(self.initiator)), 1
        )

    def test_withdraw(self):
        self.participant.states.withdraw(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.withdrawn.value)
        self.assertFalse(
            self.event.followers.filter(user=self.participant.user).exists()
        )

        self.assertEqual(
            len(self.messages(self.user)), 1
        )

    def test_reapply(self):
        self.participant.states.withdraw(save=True)
        self.participant.states.reapply(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.participant.user)), 2
        )
        self.assertEqual(
            [
                'You were added to the event "{}"'.format(self.event.title),
                'You were added to the event "{}"'.format(self.event.title)
            ],
            [
                m.subject for m in self.messages(self.participant.user)
            ]
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

    def test_accept(self):
        self.participant.states.reject(save=True)
        self.participant.states.accept(save=True)
        self.assertEqual(self.participant.status, ParticipantStateMachine.new.value)
        self.assertTrue(
            self.event.followers.filter(user=self.participant.user).exists()
        )
        self.assertEqual(
            len(self.messages(self.participant.user)), 3
        )
        self.assertEqual(

            [
                u'You were added to the event "{}"'.format(self.event.title),
                u'You have been rejected for the event "{}"'.format(self.event.title),
                u'You were added to the event "{}"'.format(self.event.title)
            ],
            [
                m.subject for m in self.messages(self.participant.user)
            ]
        )

    def test_created_passed(self):
        self.assertEqual(self.passed_participant.status, ParticipantStateMachine.succeeded.value)
        self.assertEqual(self.passed_participant.time_spent, self.passed_event.duration)

        self.assertTrue(
            self.passed_event.followers.filter(user=self.passed_participant.user).exists()
        )

        self.passed_event.refresh_from_db()
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
