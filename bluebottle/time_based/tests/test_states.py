from datetime import timedelta

from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.activities.tests.factories import TeamFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.states import (
    DateStateMachine, TimeBasedStateMachine, PeriodStateMachine, DateActivitySlotStateMachine,
    PeriodParticipantStateMachine
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory, DateActivitySlotFactory,
)


class TimeBasedActivityStatesTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.initiative.states.submit(save=True)
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
        self.initiative.states.approve(save=True)

        self.activity.states.reject()
        self.activity.states.restore()

        if self.activity.states.submit:
            self.assertTrue(
                TimeBasedStateMachine.submit in
                self.activity.states.possible_transitions()
            )
        else:
            self.assertTrue(
                DateStateMachine.publish in
                self.activity.states.possible_transitions()
            )

        self.assertTrue(
            TimeBasedStateMachine.delete in
            self.activity.states.possible_transitions()
        )

    def test_succeeded(self):
        self.initiative.states.approve(save=True)
        if self.activity.states.submit:
            self.activity.states.submit(save=True)
        else:
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
        self.initiative.states.approve(save=True)
        if self.activity.states.submit:
            self.activity.states.submit(save=True)
        else:
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
        self.initiative.states.approve(save=True)
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


class PeriodActivityStatesTestCase(TimeBasedActivityStatesTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def test_approved(self):
        if self.activity.states.submit:
            self.activity.states.submit(save=True)

        self.initiative.states.approve(save=True)

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

    def test_submitted(self):
        self.activity.states.submit()
        self.assertTrue(
            TimeBasedStateMachine.auto_approve in
            self.activity.states.possible_transitions()
        )

        self.assertTrue(
            TimeBasedStateMachine.reject in
            self.activity.states.possible_transitions()
        )

    def test_succeed_manually_no_participants(self):
        self.activity.duration_period = 'weeks'
        self.activity.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.assertFalse(
            PeriodStateMachine.succeed_manually in
            self.activity.states.possible_transitions()
        )

    def test_succeed_manually_overall(self):
        self.activity.duration_period = 'overall'

        self.activity.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.assertTrue(
            PeriodStateMachine.succeed_manually in
            self.activity.states.possible_transitions()
        )

    def test_succeed_manually_(self):
        self.activity.duration_period = 'weeks'

        self.activity.states.submit(save=True)
        self.initiative.states.approve(save=True)
        self.participant_factory.create(activity=self.activity)

        self.activity.refresh_from_db()

        self.activity.states.succeed_manually()
        self.assertEqual(
            self.activity.status, 'succeeded'
        )
        self.assertTrue(
            PeriodStateMachine.cancel in
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


class PeriodParticipantStatesTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user, status='approved')
        self.activity = PeriodActivityFactory.create(
            initiative=self.initiative,
            status='open'
        )
        self.participant = PeriodParticipantFactory.create(activity=self.activity)

    def test_stop(self):
        self.assertTrue(
            PeriodParticipantStateMachine.stop in
            self.participant.states.possible_transitions()
        )

    def test_stop_team(self):
        self.participant.team = TeamFactory.create()
        self.participant.save()

        self.assertTrue(
            PeriodParticipantStateMachine.stop not in
            self.participant.states.possible_transitions()
        )
