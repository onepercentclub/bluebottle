from bluebottle.test.utils import BluebottleTestCase
from bluebottle.deeds.tests.factories import DeedParticipantFactory, DeedFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory


class CreateEffortContributionTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = DeedFactory.create(target=10, enable_impact=True)
        self.activity.initiative.states.submit()
        self.activity.initiative.states.approve(save=True)

        self.impact_goal = ImpactGoalFactory.create(
            activity=self.activity,
            target=100,
            participant_target=10,
            realized=0,
        )
        self.activity.states.publish(save=True)

        participant = DeedParticipantFactory.create(activity=self.activity)
        self.contribution = participant.contributions.first()

    def test_status_new(self):
        self.assertEqual(self.impact_goal.realized_from_contributions, None)

    def test_status_succeed(self):
        self.contribution.states.succeed(save=True)
        self.impact_goal.refresh_from_db()
        self.assertEqual(self.impact_goal.realized_from_contributions, 10.0)

    def test_status_fail(self):
        self.test_status_succeed()
        self.contribution.states.fail(save=True)
        self.impact_goal.refresh_from_db()
        self.assertEqual(self.impact_goal.realized_from_contributions, None)
