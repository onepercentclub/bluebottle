from datetime import timedelta

from django.core import mail
from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.states import (
    DateStateMachine, TimeBasedStateMachine, DateActivitySlotStateMachine
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateParticipantFactory, DateActivitySlotFactory, DeadlineActivityFactory,
    DeadlineRegistrationFactory,
)


class TimeBasedActivityStatesTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user, status='approved')
        self.activity = self.factory.create(initiative=self.initiative)

    def test_initial(self):
        self.assertEqual(
            self.activity.status, 'draft'
        )
        if self.activity.states.submit:
            self.assertTrue(
                TimeBasedStateMachine.submit in
                self.activity.states.possible_transitions()
            )

        self.assertTrue(
            TimeBasedStateMachine.delete in
            self.activity.states.possible_transitions()
        )

        self.assertTrue(
            TimeBasedStateMachine.reject in
            self.activity.states.possible_transitions()
        )

    def test_initial_incomplete(self):
        self.activity.title = ''
        self.assertTrue(
            TimeBasedStateMachine.submit not in
            self.activity.states.possible_transitions()
        )
        self.assertTrue(
            DateStateMachine.publish not in
            self.activity.states.possible_transitions()
        )

    def test_deleted(self):
        self.activity.states.delete()
        self.assertTrue(
            TimeBasedStateMachine.restore in
            self.activity.states.possible_transitions()
        )

    def test_rejected(self):
        self.activity.states.reject()
        self.assertTrue(
            TimeBasedStateMachine.restore in
            self.activity.states.possible_transitions()
        )

    def test_needs_work(self):
        self.activity.states.reject()
        self.activity.states.restore()

        self.assertTrue(
            DateStateMachine.publish in
            self.activity.states.possible_transitions()
        )

        self.assertTrue(
            TimeBasedStateMachine.delete in
            self.activity.states.possible_transitions()
        )

    def test_succeeded(self):
        self.activity.states.publish(save=True)
        self.activity.refresh_from_db()
        self.activity.states.succeed()
        self.assertEqual(
            self.activity.status, 'succeeded'
        )
        self.assertTrue(
            TimeBasedStateMachine.cancel in
            self.activity.states.possible_transitions()
        )

    def test_cancelled(self):
        self.activity.states.publish(save=True)
        self.activity.refresh_from_db()
        self.activity.states.cancel()
        self.assertEqual(
            self.activity.status, 'cancelled'
        )
        self.assertTrue(
            TimeBasedStateMachine.restore in
            self.activity.states.possible_transitions()
        )


class DateActivityStatesTestCase(TimeBasedActivityStatesTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def test_approved(self):
        self.activity.states.publish(save=True)

        self.activity.refresh_from_db()
        self.assertEqual(
            self.activity.status, 'open'
        )
        self.assertTrue(
            TimeBasedStateMachine.cancel in
            self.activity.states.possible_transitions()
        )

        self.assertTrue(
            TimeBasedStateMachine.succeed in
            self.activity.states.possible_transitions()
        )

        organizer = self.activity.contributors.instance_of(Organizer).get()
        self.assertEqual(
            organizer.status,
            'succeeded'
        )
        self.assertEqual(organizer.contributions.first().contribution_type, 'organizer')
        organizer_contribution = organizer.contributions.get()
        self.assertEqual(
            organizer_contribution.status,
            'succeeded'
        )
        self.assertAlmostEqual(
            organizer_contribution.start,
            now(),
            delta=timedelta(minutes=2)
        )

    def test_initial_only_incomplete_slots(self):
        slot = self.activity.slots.first()
        slot.duration = None
        slot.save()
        DateActivitySlotFactory.create(
            activity=self.activity,
            duration=None
        )

        self.assertTrue(
            DateStateMachine.publish not in
            self.activity.states.possible_transitions()
        )

    def test_initial_one_complete_slot(self):
        DateActivitySlotFactory.create(
            activity=self.activity,
            duration=timedelta(hours=2)
        )
        self.assertTrue(
            DateStateMachine.publish in
            self.activity.states.possible_transitions()
        )


class DateActivitySlotStatesTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.initiative.states.submit(save=True)
        self.activity = DateActivityFactory.create(
            initiative=self.initiative,
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
        )

    def test_initial(self):
        self.assertEqual(
            self.slot.status, 'open'
        )
        self.assertTrue(
            DateActivitySlotStateMachine.cancel in
            self.slot.states.possible_transitions()
        )

    def test_cancel(self):
        self.slot.states.cancel(save=True)
        self.assertEqual(
            self.slot.status, 'cancelled'
        )
        self.assertTrue(
            DateActivitySlotStateMachine.reopen in
            self.slot.states.possible_transitions()
        )

    def test_reopen(self):
        self.test_cancel()
        self.slot.states.reopen(save=True)
        self.assertEqual(
            self.slot.status, 'open'
        )
        self.assertTrue(
            DateActivitySlotStateMachine.cancel in
            self.slot.states.possible_transitions()
        )


class DeadlineRegistrationStatesTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user, status='approved')
        self.activity = DeadlineActivityFactory.create(
            initiative=self.initiative,
            preparation=None,
            duration=timedelta(hours=4),
            title='Some good stuff',
            status='open'
        )

    def test_register(self):
        mail.outbox = []
        registration = DeadlineRegistrationFactory.create(
            activity=self.activity,
            user=self.user,
            as_user=self.user
        )
        self.assertEqual(
            registration.status,
            'accepted'
        )
        self.assertEqual(len(mail.outbox), 2)
        subjects = [message.subject for message in mail.outbox]

        self.assertTrue(
            'You have a new participant for your activity "Some good stuff" 🎉' in subjects
        )

        self.assertTrue(
            'You have joined the activity "Some good stuff"' in subjects
        )

        participants = registration.deadlineparticipant_set
        participant = participants.first()
        self.assertEqual(participants.count(), 1)
        self.assertEqual(participant.status, 'succeeded')
        self.assertEqual(participant.contributions.count(), 1)
        self.assertEqual(participant.contributions.first().status, 'succeeded')

    def test_register_review(self):
        mail.outbox = []
        self.activity.review = True
        self.activity.save()
        registration = DeadlineRegistrationFactory.create(
            activity=self.activity,
            user=self.user,
            as_user=self.user
        )
        self.assertEqual(
            registration.status,
            'new'
        )
        self.assertEqual(len(mail.outbox), 2)

        participants = registration.deadlineparticipant_set
        participant = participants.first()
        self.assertEqual(participants.count(), 1)
        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.contributions.count(), 1)
        self.assertEqual(participant.contributions.first().status, 'new')
