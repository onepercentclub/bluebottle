from datetime import timedelta

from django.utils.timezone import now

from bluebottle.activities.models import Organizer
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
)
from bluebottle.time_based.states import TimeBasedStateMachine
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


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
            TimeBasedStateMachine.submit in
            self.activity.states.possible_transitions()
        )

        self.assertTrue(
            TimeBasedStateMachine.delete in
            self.activity.states.possible_transitions()
        )

    def test_approved(self):
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

    def test_succeeded(self):
        self.activity.states.submit(save=True)
        self.initiative.states.approve(save=True)
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
        self.activity.states.submit(save=True)
        self.initiative.states.approve(save=True)
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


class PeriodActivityStatesTestCase(TimeBasedActivityStatesTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
