from datetime import timedelta
from django.utils.timezone import now

from bluebottle.fsm import TransitionNotAllowed
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory


class EventTransitionOpenTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventTransitionOpenTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.initiative.submit()
        self.initiative.save()

        self.event = EventFactory.create(title='', initiative=self.initiative)

    def test_default_status(self):
        self.assertEqual(
            self.event.status, Event.Status.draft
        )

    def test_complete(self):
        self.initiative.approve()

        self.event.title = 'Some title'
        self.event.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, Event.Status.open
        )

    def test_complete_not_approved(self):
        self.event.title = 'Some title'
        self.event.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, Event.Status.draft
        )

    def test_approve_initiative(self, **kwargs):
        self.event.title = 'Some title'
        self.event.save()

        self.initiative.approve()
        self.initiative.save()

        event = Event.objects.get(pk=self.event.pk)

        self.assertEqual(
            event.status, Event.Status.open
        )

    def test_approve_initiatve_incomplete(self, **kwargs):
        self.initiative.approve()
        self.initiative.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(
            event.status, Event.Status.draft
        )


class EventTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventTransitionTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(
            initiative=self.initiative, capacity=1
        )
        self.initiative.submit()
        self.initiative.approve()
        self.initiative.save()

        self.event = Event.objects.get(pk=self.event.pk)

    def test_default_status(self):
        self.assertEqual(
            self.event.status, Event.Status.open
        )
        self.event._meta.fields[5].get_all_available_transitions(self.event)

    def test_full(self):
        ParticipantFactory.create(activity=self.event)

        self.assertEqual(
            self.event.status, Event.Status.full
        )

    def test_reopen(self):
        participant = ParticipantFactory.create(activity=self.event)

        self.assertEqual(
            self.event.status, Event.Status.full
        )

        participant.withdraw()
        participant.save()

        self.assertEqual(
            self.event.status, Event.Status.open
        )

    def test_start(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start = now() - timedelta(days=1)
        self.event.do_start()

        self.assertEqual(
            self.event.status,
            Event.Status.running
        )

    def test_start_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start = now() + timedelta(days=1)
        self.assertRaises(
            TransitionNotAllowed,
            self.event.do_start
        )

    def test_done(self):
        participant = ParticipantFactory.create(activity=self.event)
        self.event.start = now() - timedelta(days=1)
        self.event.do_start()
        self.event.end = now() - timedelta(days=1)
        self.event.done()

        self.assertEqual(
            self.event.status,
            Event.Status.done
        )

        participant = Participant.objects.get(pk=participant.pk)
        self.assertEqual(
            participant.status,
            Participant.Status.success
        )

    def test_done_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start = now() - timedelta(days=1)
        self.event.do_start()
        self.event.end = now() + timedelta(days=1)

        self.assertRaises(
            TransitionNotAllowed,
            self.event.done
        )

    def test_close(self):
        self.event.close()

        self.assertEqual(
            self.event.status,
            Event.Status.closed
        )

    def test_extend(self):
        self.event.close()

        self.event.start = now() + timedelta(days=1)
        self.event.extend()

        self.assertEqual(
            self.event.status,
            Event.Status.open
        )

    def test_extend_start_date_passed(self):
        self.event.close()

        self.event.start = now() - timedelta(days=1)
        self.assertRaises(
            TransitionNotAllowed,
            self.event.extend
        )


class ParticiantTransitionTestCase(BluebottleTestCase):
    pass
