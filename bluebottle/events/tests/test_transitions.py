from datetime import timedelta
from django.utils.timezone import now

from bluebottle.fsm import TransitionNotAllowed
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


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

    def test_approve_initiative_incomplete(self, **kwargs):
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
        self.event.start_time = now() - timedelta(days=1)
        self.event.start()

        self.assertEqual(
            self.event.status,
            Event.Status.running
        )

    def test_start_date_in_future(self):
        ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() + timedelta(days=1)
        self.assertRaises(
            TransitionNotAllowed,
            self.event.start
        )

    def test_done(self):
        participant = ParticipantFactory.create(activity=self.event)
        self.event.start_time = now() - timedelta(days=1)
        self.event.start()
        self.event.end_time = now() - timedelta(days=1)
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
        self.event.start_time = now() - timedelta(days=1)
        self.event.start()
        self.event.end_time = now() + timedelta(days=1)

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

    def test_redraft(self):
        self.event.close()
        self.assertEqual(
            self.event.status,
            Event.Status.closed
        )
        self.event.redraft()
        self.assertEqual(
            self.event.status,
            Event.Status.draft
        )

    def test_extend(self):
        self.event.close()

        self.event.start_time = now() + timedelta(days=1)
        self.event.extend()

        self.assertEqual(
            self.event.status,
            Event.Status.open
        )

    def test_extend_start_date_passed(self):
        self.event.close()

        self.event.start_time = now() - timedelta(days=1)
        self.assertRaises(
            TransitionNotAllowed,
            self.event.extend
        )


class ParticipantTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(ParticipantTransitionTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(
            initiative=self.initiative, capacity=1
        )
        self.initiative.submit()
        self.initiative.approve()
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
            Participant.Status.new
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_withdraw(self):
        self.participant.withdraw()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            Participant.Status.withdrawn
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_withdraw_closed_event(self):
        self.event.close()
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.withdraw
        )
        self.assertEqual(
            self.participant.status,
            Participant.Status.new
        )

    def test_reapply(self):
        self.participant.withdraw()
        self.participant.reapply()

        self.participant.save()

        self.assertEqual(
            self.participant.status,
            Participant.Status.new
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_reapply_closed_event(self):
        self.participant.withdraw()
        self.event.close()

        self.assertRaises(
            TransitionNotAllowed,
            self.participant.reapply
        )
        self.assertEqual(
            self.participant.status,
            Participant.Status.withdrawn
        )

    def test_reject(self):
        self.participant.reject()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            Participant.Status.rejected
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_success(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.start()
        self.event.done()
        self.event.save()

        self.participant.success()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            Participant.Status.success
        )
        self.assertEqual(
            len(self.event.participants), 1
        )

    def test_success_new_event(self):
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.success
        )

    def test_no_show(self):
        self.event.start_time = now() - timedelta(days=1)
        self.event.end_time = now() - timedelta(days=1)
        self.event.start()
        self.event.done()
        self.event.save()

        self.participant.success()
        self.participant.no_show()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            Participant.Status.no_show
        )
        self.assertEqual(
            len(self.event.participants), 0
        )

    def test_no_show_new(self):
        self.assertRaises(
            TransitionNotAllowed,
            self.participant.no_show
        )

    def test_close(self):
        self.participant.close()
        self.participant.save()
        self.assertEqual(
            self.participant.status,
            Participant.Status.closed
        )
        self.assertEqual(
            len(self.event.participants), 0
        )
