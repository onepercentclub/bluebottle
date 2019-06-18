from datetime import timedelta
from django.utils.timezone import now

from bluebottle.fsm import TransitionNotAllowed
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.events.models import Event, Participant
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class EventTransitionOpenTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventTransitionOpenTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.save()

        self.event = EventFactory.create(title='', initiative=self.initiative)

    def test_default_status(self):
        self.assertEqual(
            self.event.status, EventTransitions.values.draft
        )

    def test_complete(self):
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

        participant.transitions.withdraw()
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
            TransitionNotAllowed,
            self.event.transitions.start
        )

    def test_done(self):
        participant = ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.done()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.done
        )

        participant = Participant.objects.get(pk=participant.pk)
        self.assertEqual(
            participant.status,
            ParticipantTransitions.values.success
        )

    def test_done_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.end_time = now() + timedelta(days=1)

        self.assertRaises(
            TransitionNotAllowed,
            self.event.transitions.done
        )

    def test_close(self):
        self.event.transitions.close()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.closed
        )

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
            TransitionNotAllowed,
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
        self.participant.transitions.withdraw()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.withdrawn
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_withdraw_closed_event(self):
        self.event.transitions.close()
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.withdraw
        )
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.new
        )

    def test_reapply(self):
        self.participant.transitions.withdraw()
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
        self.participant.transitions.withdraw()
        self.event.transitions.close()

        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.reapply
        )
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.withdrawn
        )

    def test_reject(self):
        self.participant.transitions.reject()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.rejected
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_success(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.transitions.done()
        self.event.save()

        self.participant.transitions.success()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            ParticipantTransitions.values.success
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_success_new_event(self):
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.transitions.success
        )

    def test_no_show(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.transitions.start()
        self.event.transitions.done()
        self.event.save()

        self.participant.transitions.success()
        self.participant.transitions.no_show()
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
            TransitionNotAllowed,
            self.participant.transitions.no_show
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
