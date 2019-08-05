from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.fsm import TransitionNotAllowed, TransitionNotPossible
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class EventTransitionOpenTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventTransitionOpenTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.save()

        user = BlueBottleUserFactory.create(first_name='Nono')
        self.event = EventFactory.create(title='', initiative=self.initiative, owner=user)

    def test_default_status(self):
        self.assertEqual(
            self.event.status, EventTransitions.values.draft
        )

    def test_open(self):
        self.initiative.transitions.approve()

        self.event.title = 'Some title'
        self.event.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, EventTransitions.values.open
        )

    def test_complete_not_approved(self):
        self.event.title = 'Some title'
        self.event.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, EventTransitions.values.draft
        )

    def test_approve_initiative(self, **kwargs):
        self.event.title = 'Some title'
        self.event.save()

        self.initiative.transitions.approve()
        self.initiative.save()

        event = Event.objects.get(pk=self.event.pk)

        self.assertEqual(
            event.status, EventTransitions.values.open
        )

    def test_approve_initiative_incomplete(self, **kwargs):
        self.initiative.transitions.approve()
        self.initiative.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, EventTransitions.values.draft
        )


class EventTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventTransitionTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(
            initiative=self.initiative, capacity=1
        )
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        self.event = Event.objects.get(pk=self.event.pk)

    def test_default_status(self):
        self.assertEqual(
            self.event.status, EventTransitions.values.open
        )

    def test_full(self):
        ParticipantFactory.create(activity=self.event)

        self.assertEqual(
            self.event.status, EventTransitions.values.full
        )

    def test_reopen(self):
        participant = ParticipantFactory.create(activity=self.event)

        self.assertEqual(
            self.event.status, EventTransitions.values.full
        )

        participant.transitions.withdraw(user=participant.user)
        participant.save()

        self.assertEqual(
            self.event.status, EventTransitions.values.open
        )

    def test_start(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.transitions.start()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.running
        )

    def test_start_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() + timedelta(days=1)
        self.assertRaises(
            TransitionNotPossible,
            self.event.transitions.start
        )

    def test_succeeded(self):
        participant = ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.succeed()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.succeeded
        )

        participant = Participant.objects.get(pk=participant.pk)
        self.assertEqual(
            participant.status,
            ParticipantTransitions.values.succeeded
        )

    def test_succeeded_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.end_time = now() + timedelta(days=1)

        self.assertRaises(
            TransitionNotPossible,
            self.event.transitions.succeed
        )

    def test_close(self):
        self.event.transitions.close()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.closed
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Your event has been closed")
        self.assertTrue("Hi Nono,", mail.outbox[1].body)

    def test_redraft(self):
        self.event.transitions.close()
        self.assertEqual(
            self.event.status,
            EventTransitions.values.closed
        )
        self.event.transitions.redraft()
        self.assertEqual(
            self.event.status,
            EventTransitions.values.draft
        )

    def test_extend(self):
        self.event.transitions.close()

        self.event.start_time = now() + timedelta(days=1)
        self.event.transitions.extend()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.open
        )

    def test_extend_start_date_passed(self):
        self.event.transitions.close()

        self.event.start_time = now() - timedelta(days=1)
        self.assertRaises(
            TransitionNotPossible,
            self.event.transitions.extend
        )


class ParticipantTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(ParticipantTransitionTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(
            initiative=self.initiative, capacity=1
        )
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        self.event = Event.objects.get(pk=self.event.pk)

        self.user = BlueBottleUserFactory.create()

        self.participant = ParticipantFactory.create(
            activity=self.event,
            user=self.user
        )

    def test_new(self):
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.new
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_withdraw(self):
        self.participant.transitions.withdraw(user=self.participant.user)
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.withdrawn
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_withdraw_other_user(self):
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.withdraw,
            user=self.event.owner
        )

    def test_withdraw_closed_event(self):
        self.event.transitions.close()
        self.assertRaises(
            TransitionNotPossible,
            self.participant.transitions.withdraw
        )
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.new
        )

    def test_reapply(self):
        self.participant.transitions.withdraw(user=self.participant.user)
        self.participant.transitions.reapply()

        self.participant.save()

        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.new
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_reapply_closed_event(self):
        self.participant.transitions.withdraw(user=self.participant.user)
        self.event.transitions.close()

        self.assertRaises(
            TransitionNotPossible,
            self.participant.transitions.reapply
        )
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.withdrawn
        )

    def test_reject(self):
        self.participant.transitions.reject(self.event.initiative.activity_manager)
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.rejected
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_untreject(self):
        self.participant.transitions.reject(self.event.initiative.activity_manager)
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.rejected
        )
        self.participant.transitions.unreject(self.event.initiative.activity_manager)
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.new
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_reject_no_owner(self):
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.reject,
            user=self.participant.user
        )

    def test_success(self):
        self.event.start_time = now() - timedelta(days=2)
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.transitions.succeed()
        self.event.save()

        self.participant.transitions.succeed()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.succeeded
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_success_new_event(self):
        self.assertRaises(
            TransitionNotPossible,
            self.participant.transitions.succeed
        )

    def test_no_show(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.transitions.succeed()
        self.event.save()

        self.participant.transitions.succeed()
        self.participant.transitions.no_show(user=self.event.initiative.activity_manager)

        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.no_show
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_no_show_new(self):
        self.assertRaises(
            TransitionNotPossible,
            self.participant.transitions.no_show,
            user=self.initiative.activity_manager
        )

    def test_no_show_other_user(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.transitions.succeed()
        self.event.save()

        self.participant.transitions.succeed()

        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.no_show,
            user=self.participant.user
        )

    def test_close(self):
        self.participant.transitions.close()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.closed
        )
        self.assertEqual(
            len(self.event.participants), 0
        )


class EventTransitionValidationTestCase(BluebottleTestCase):

    def test_not_online_requires_location(self):
        event = EventFactory.create(
            location=None,
            is_online=False
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.draft
        )
        self.assertEqual(event.transitions.is_complete(), [u"Location is required or select 'is online'"])

        self.assertRaises(
            TransitionNotPossible,
            event.transitions.open
        )

    def test_wrong_end_date(self):
        event = EventFactory.create(
            registration_deadline=now() + timedelta(weeks=3),
            start_time=now() + timedelta(weeks=2),
            end_time=now() + timedelta(weeks=1),
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.draft
        )
        self.assertEqual(event.transitions.is_complete(), [u"End time should be after start time"])

        self.assertRaises(
            TransitionNotPossible,
            event.transitions.open
        )

    def test_wrong_registration_deadline(self):
        event = EventFactory.create(
            registration_deadline=now() + timedelta(weeks=3),
            start_time=now() + timedelta(weeks=2),
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.draft
        )
        self.assertEqual(event.transitions.is_complete(), [u"Registration deadline should be before start time"])

        self.assertRaises(
            TransitionNotPossible,
            event.transitions.open
        )

    def test_empty_registration_deadline(self):
        # Test that validation doesn't trip if registration deadline isn't filled in
        event = EventFactory.create(
            registration_deadline=None,
            start_time=now() + timedelta(weeks=2),
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.draft
        )
        self.assertEqual(event.transitions.is_complete(), None)
