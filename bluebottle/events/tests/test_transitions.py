from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.events.models import Event, Participant
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.events.transitions import EventTransitions, ParticipantTransitions
from bluebottle.fsm import TransitionNotAllowed, TransitionNotPossible
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.transitions import ReviewTransitions
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
            self.event.status, EventTransitions.values.in_review
        )

    def test_open(self):
        self.initiative.transitions.approve()

        self.event.title = 'Some title'
        self.event.review_transitions.submit()
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
            event.status, EventTransitions.values.in_review
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
            event.status, EventTransitions.values.in_review
        )


class EventReviewTransitionTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventReviewTransitionTestCase, self).setUp()

        self.initiative = InitiativeFactory.create()
        self.initiative.save()

        self.event = EventFactory.create(initiative=self.initiative, owner=self.initiative.owner)

    def test_submit_initiative(self):
        self.initiative.transitions.submit()
        self.event.refresh_from_db()

        self.assertEqual(self.initiative.status, ReviewTransitions.values.submitted)
        self.assertEqual(self.event.review_status, ReviewTransitions.values.submitted)
        self.assertEqual(self.event.status, EventTransitions.values.in_review)

    def test_submit_incomplete_activity(self):
        self.event.title = ''
        self.event.save()
        self.initiative.transitions.submit()

        self.event.refresh_from_db()

        self.assertEqual(self.initiative.status, ReviewTransitions.values.submitted)
        self.assertEqual(self.event.review_status, ReviewTransitions.values.draft)
        self.assertEqual(self.event.status, EventTransitions.values.in_review)

    def test_approve_initiative(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event.refresh_from_db()

        self.assertEqual(self.initiative.status, ReviewTransitions.values.approved)
        self.assertEqual(self.event.review_status, ReviewTransitions.values.approved)
        self.assertEqual(self.event.status, EventTransitions.values.open)

    def test_approve_event_after_initiative(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        event = EventFactory.create(initiative=self.initiative, owner=self.initiative.owner)
        event.review_transitions.submit()

        self.assertEqual(event.review_status, ReviewTransitions.values.approved)
        self.assertEqual(event.status, EventTransitions.values.open)

    def test_close_initiative(self):
        self.initiative.transitions.submit()
        self.initiative.transitions.close()

        self.event.refresh_from_db()
        self.assertEqual(self.event.review_status, ReviewTransitions.values.closed)


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
        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()
        self.event.transitions.start()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.running
        )

    def test_start_date_in_future(self):
        ParticipantFactory.create(activity=self.event)

        start = now() + timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()

        self.assertRaises(
            TransitionNotPossible,
            self.event.transitions.start
        )

    def test_succeeded(self):
        participant = ParticipantFactory.create(activity=self.event)

        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()
        self.event.duration = 12
        self.event.save()

        self.event.transitions.start()
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
        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()

        self.event.transitions.start()
        self.event.duration = 48

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

    def test_extend(self):
        self.event.transitions.close()

        start = now() + timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()

        self.event.transitions.extend()

        self.assertEqual(
            self.event.status,
            EventTransitions.values.open
        )

    def test_extend_start_date_passed(self):
        self.event.transitions.close()

        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()

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
        start = now() - timedelta(days=2)
        self.event.start_time = start.time()
        self.event.start_date = start.date()
        self.event.duration = 24
        self.event.save()

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
        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()
        self.event.duration = 12
        self.event.save()

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
        start = now() - timedelta(days=1)
        self.event.start_time = start.time()
        self.event.start_date = start.date()
        self.event.duration = 12
        self.event.save()

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
            EventTransitions.values.in_review
        )
        errors = event.review_transitions.is_valid()
        self.assertEqual(
            unicode(errors[0]),
            u"This field is required or select 'Online'"
        )

        self.assertRaises(
            TransitionNotPossible,
            event.review_transitions.submit
        )

    def test_wrong_registration_deadline(self):
        start = now() - timedelta(weeks=2)
        event = EventFactory.create(
            registration_deadline=(now() + timedelta(weeks=3)).date(),
            start_time=start.time(),
            start_date=start.date(),
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.in_review
        )
        errors = event.review_transitions.is_valid()
        self.assertEqual(
            unicode(errors[0]),
            u"Registration deadline should be before the start time"
        )

        self.assertRaises(
            TransitionNotPossible,
            event.review_transitions.submit
        )

    def test_empty_registration_deadline(self):
        # Test that validation doesn't trip if registration deadline isn't filled in
        start = now() - timedelta(weeks=2)
        event = EventFactory.create(
            registration_deadline=None,
            start_time=start.time(),
            start_date=start.date(),
        )
        self.assertEqual(
            event.status,
            EventTransitions.values.in_review
        )
        self.assertEqual(event.review_transitions.is_complete(), None)
