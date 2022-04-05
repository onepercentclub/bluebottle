import uuid
from bluebottle.test.utils import TriggerTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.activities.messages import TeamAddedMessage, TeamCancelledMessage, TeamReopenedMessage
from bluebottle.activities.effects import TeamContributionTransitionEffect
from bluebottle.activities.tests.factories import TeamFactory

from bluebottle.time_based.tests.factories import PeriodActivityFactory, PeriodParticipantFactory
from bluebottle.time_based.states import TimeContributionStateMachine


class TeamTriggersTestCase(TriggerTestCase):
    factory = TeamFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.activity = PeriodActivityFactory.create()
        self.activity.initiative.states.submit(save=True)
        self.activity.initiative.states.approve(save=True)
        self.activity.refresh_from_db()

        self.staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.defaults = {
            'activity': self.activity,
        }
        super().setUp()

    def create(self):
        super().create()

        self.participant = PeriodParticipantFactory.create(
            activity=self.activity,
            user=self.model.owner,
            team=self.model
        )

    def test_initiate(self):
        self.model = self.factory.build(**self.defaults)

        with self.execute():
            self.assertEqual(self.model.status, 'open')
            self.assertNotificationEffect(TeamAddedMessage)
            self.assertTrue(isinstance(self.model.id, uuid.UUID))

    def test_cancel(self):
        self.create()

        self.model.states.cancel()

        with self.execute():
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.fail))
            self.assertNotificationEffect(TeamCancelledMessage)

        self.model.save()
        self.participant.refresh_from_db()

        for contribution in self.participant.contributions.all():
            self.assertEqual(contribution.status, TimeContributionStateMachine.failed.value)

    def test_reopen(self):
        self.create()

        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNotificationEffect(TeamReopenedMessage)
            self.assertEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.succeed))

    def test_reopen_withdrawn(self):
        self.create()

        self.participant.states.withdraw(save=True)
        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNoEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.succeed))

    def test_reopen_cancelled_activity(self):
        self.create()

        self.activity.states.cancel(save=True)
        self.model.states.cancel(save=True)
        self.model.states.reopen()

        with self.execute():
            self.assertNoEffect(TeamContributionTransitionEffect(TimeContributionStateMachine.succeed))
